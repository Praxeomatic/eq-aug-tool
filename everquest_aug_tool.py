import streamlit as st
import pandas as pd
import re
import csv
import io
import numpy as np

# === Styling ===
st.markdown("""
    <style>
    .block-container { padding: 1rem 1.5rem; max-width: 100% !important; }
    section[data-testid="stSidebar"] { width: 240px !important; padding-right: 0rem !important; }
    .css-1d391kg { padding-left: 1rem !important; padding-right: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# === Canonical Equipment Slots ===
EQUIPPED_SLOTS = [
    "Charm", "Ear-1", "Ear-2", "Head", "Face", "Neck", "Shoulders", "Arms", "Back",
    "Wrist-1", "Wrist-2", "Range", "Hands", "Primary", "Secondary",
    "Finger-1", "Finger-2", "Chest", "Legs", "Feet", "Waist", "Power Source"
]
EQUIPPED_BASE_SLOTS = list(set([s.split('-')[0] for s in EQUIPPED_SLOTS]))

STAT_MAP = {
    "ac": "AC", "hp": "HP", "mana": "Mana", "attack": "Atk",
    "heroic_str": "HStr", "heroic_sta": "HSta", "heroic_agi": "HAgi",
    "heroic_dex": "HDex", "heroic_wis": "HWis", "heroic_int": "HInt",
}
STAT_COLS = list(STAT_MAP.keys())
UI_COLS = list(STAT_MAP.values())

DEFAULT_WEIGHTS = {
    "AC": 10.0, "HP": 1.0, "Mana": 0.0, "Atk": 1.0,
    "HStr": 15.0, "HSta": 20.0, "HAgi": 20.0, "HDex": 20.0,
    "HWis": 4.0, "HInt": 0.0
}

@st.cache_data
def load_aug_db():
    df = pd.read_csv("augmentation_only_items.csv")
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.set_index("id")
    return df[df["charmfile"].isna() | (df["charmfile"].str.strip() == "")]

aug_db = load_aug_db()

# === Sidebar Weights ===
st.sidebar.header("Stat Weights")
st.sidebar.caption("Adjust stat weights")

multipliers = {
    ui: st.sidebar.number_input(
        ui,
        value=DEFAULT_WEIGHTS.get(ui, 1.0),
        step=0.1,
        format="%.1f",
        key=f"weight_{ui}"
    ) for ui in UI_COLS
}

st.title("EverQuest Augment Analyzer")
uploaded = st.file_uploader("Upload your `/output inventory` file", type="txt")

def parse_inventory(txt_bytes):
    rows = []
    try:
        inventory_text = txt_bytes.decode("utf-8")
        file_io = io.StringIO(inventory_text)
        reader = csv.reader(file_io, delimiter='\t')
        next(reader, None)
        for line in reader:
            if len(line) != 5: continue
            loc, name, item_id, count, slots = line
            if name.strip() == "Empty" or item_id.strip() == "0": continue
            rows.append({
                "OriginalLocation": loc.strip(), "Name": name.strip().rstrip('*'), "ID": int(item_id),
            })
    except Exception as e:
        st.error(f"Failed to parse inventory file. Error: {e}")
        return pd.DataFrame()
    return pd.DataFrame(rows)

def normalize_base_slot(label):
    base_slot = label.strip().split('-')[0].title()
    if base_slot == "Fingers": base_slot = "Finger"
    if base_slot == "Ears": base_slot = "Ear"
    if base_slot == "Wrists": base_slot = "Wrist"
    return base_slot

# --- IMPROVEMENT: Helper function to format the dataframe just for display ---
def format_for_display(df_in):
    """Creates a copy of a dataframe and formats numeric columns into clean strings."""
    df_out = df_in.copy()
    cols_to_format = ["Score"] + UI_COLS
    
    for col in cols_to_format:
        if col in df_out.columns:
            # Apply formatting: Convert numbers to integer-strings, and NaNs to empty strings
            df_out[col] = df_out[col].apply(lambda x: f'{x:.0f}' if pd.notna(x) else '')
            
    return df_out

# === Main Logic ===
if uploaded:
    parsed = parse_inventory(uploaded.getvalue())
    if not parsed.empty:
        parsed_augs = parsed[parsed["ID"].isin(aug_db.index)].copy()
        if parsed_augs.empty:
            st.warning("No augmentations from your inventory file were found in the item database.")
            st.stop()
        
        parsed_augs = parsed_augs.merge(aug_db, how="left", left_on="ID", right_index=True)
        parsed_augs["SlotLabel"] = parsed_augs["OriginalLocation"].apply(normalize_base_slot)

        equipped_rows = parsed_augs[parsed_augs["SlotLabel"].isin(EQUIPPED_BASE_SLOTS)].copy()
        unequipped_rows = parsed_augs[~parsed_augs.index.isin(equipped_rows.index)].copy()
        
        dupe_slots = ["Ear", "Wrist", "Finger"]
        for slot in dupe_slots:
            slot_indices = equipped_rows[equipped_rows['SlotLabel'] == slot].index
            for i, dataframe_index in enumerate(slot_indices):
                equipped_rows.loc[dataframe_index, 'SlotLabel'] = f"{slot}-{i+1}"

        for df in [equipped_rows, unequipped_rows]:
            df['Score'] = 0.0
            for stat_col in STAT_COLS:
                if stat_col in df.columns:
                    df[stat_col] = pd.to_numeric(df[stat_col], errors='coerce').fillna(0)
                    ui_label = STAT_MAP[stat_col]
                    df['Score'] += df[stat_col] * multipliers[ui_label]

            df["Focus"] = df.get("focusname", "")
            df.rename(columns=STAT_MAP, inplace=True)
            existing_ui_cols = [col for col in UI_COLS if col in df.columns]
            df[existing_ui_cols] = df[existing_ui_cols].replace(0, np.nan)

        # --- Display Logic ---
        st.subheader("Equipped Augs")
        equipped_template = pd.DataFrame({"SlotLabel": EQUIPPED_SLOTS})
        equipped_df = equipped_template.merge(equipped_rows, on="SlotLabel", how="left")
        
        display_cols = ["SlotLabel", "Name", "Score"] + UI_COLS + ["Focus"]
        equipped_df_display = equipped_df.reindex(columns=display_cols)
        
        equipped_df_display['Name'] = equipped_df_display['Name'].fillna('Empty')
        equipped_df_display['Score'] = equipped_df_display['Score'].fillna(0)
        equipped_df_display['Focus'] = equipped_df_display['Focus'].fillna('')
        
        # Sort the numeric data first, then format the result for display
        equipped_sorted = equipped_df_display.sort_values("Score", ascending=False)
        st.dataframe(
            format_for_display(equipped_sorted), 
            hide_index=True, 
            use_container_width=True
        )

        st.subheader("Unequipped Augs")
        unequipped_rows = unequipped_rows.rename(columns={"OriginalLocation": "Location"})
        unequipped_display_cols = ["Location", "Name", "Score"] + UI_COLS + ["Focus"]
        unequipped_rows_display = unequipped_rows.reindex(columns=unequipped_display_cols)
        
        # Sort the numeric data first, then format the result for display
        unequipped_sorted = unequipped_rows_display.sort_values("Score", ascending=False)
        st.dataframe(
            format_for_display(unequipped_sorted),
            hide_index=True, 
            use_container_width=True
        )