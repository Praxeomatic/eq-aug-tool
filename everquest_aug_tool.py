import streamlit as st
import pandas as pd

# Load the internal augmentation database
@st.cache_data
def load_aug_db():
    df = pd.read_csv("augmentation_only_items.csv", low_memory=False)
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    # Exclude ornaments using charmfile field only
    if "charmfile" in df.columns:
        df = df[df["charmfile"].isna() | (df["charmfile"].astype(str).str.strip() == "")]

    return df.set_index("id")

aug_db = load_aug_db()

# Stat multipliers (sidebar)
default_multipliers = {
    "AC": 1,
    "HP": 1,
    "Mana": 1,
    "HSta": 1,
    "HStr": 1,
    "HAgi": 1,
    "HDex": 1,
    "HWis": 1,
    "HInt": 1,
}

st.sidebar.header("Stat Multipliers")
multipliers = {}
for stat, default in default_multipliers.items():
    multipliers[stat] = st.sidebar.number_input(stat, value=default)

# Upload section
st.title("EverQuest Aug Tool")
uploaded_file = st.file_uploader("Upload your EverQuest /output inventory .txt file", type="txt")

# Aug extraction from raw text
EQUIP_SLOTS = {
    "Charm", "Ear", "Head", "Face", "Neck", "Shoulders", "Arms", "Back", "Wrist",
    "Range", "Hands", "Primary", "Secondary", "Fingers", "Chest", "Legs", "Feet", "Waist"
}

def extract_augs_from_inventory(txt_file):
    aug_rows = []
    lines = txt_file.getvalue().decode("utf-8").splitlines()
    current_slot = None
    equipped_item_present = False
    slot_counters = {"Ear": 0, "Wrist": 0, "Fingers": 0}

    for line in lines:
        parts = line.strip().split("\t")
        if len(parts) != 5:
            continue

        location, name, item_id, count, slots = parts

        if "-Slot" not in location:
            equipped_item_present = location in EQUIP_SLOTS and name != "Empty" and item_id != "0"
            if equipped_item_present:
                label = location
                if location in slot_counters:
                    slot_counters[location] += 1
                    label = f"{location}{slot_counters[location]}"
                current_slot = label
            else:
                current_slot = None

        elif "-Slot" in location and name != "Empty" and item_id != "0":
            try:
                item_id_int = int(item_id)
                if equipped_item_present and item_id_int in aug_db.index:
                    aug_rows.append({
                        "ID": item_id_int,
                        "Name": name,
                        "Equipped": True,
                        "ParentSlot": current_slot
                    })
            except ValueError:
                continue

    return pd.DataFrame(aug_rows)

# Score function
def compute_score(row, multipliers):
    return sum(row[stat] * multipliers[stat] for stat in multipliers)

# Process uploaded file
if uploaded_file:
    inv_df = extract_augs_from_inventory(uploaded_file)

    if inv_df.empty:
        st.error("No augmentations found in this file.")
    else:
        inv_df = inv_df[inv_df["ID"].isin(aug_db.index)]
        merged = pd.merge(inv_df, aug_db, how="inner", left_on="ID", right_index=True)

        for stat in default_multipliers:
            if stat.lower() in merged.columns:
                merged[stat] = pd.to_numeric(merged[stat.lower()], errors="coerce").fillna(0)
            else:
                merged[stat] = 0

        merged["Score"] = merged.apply(lambda row: compute_score(row, multipliers), axis=1)
        merged["FocusEffect"] = merged.get("focusname", "")

        st.subheader("Equipped Augmentations (Scored)")
        display_cols = ["ParentSlot", "Name", "ID", "Score"] + list(default_multipliers.keys()) + ["FocusEffect"]
        st.dataframe(
            merged[display_cols]
            .sort_values(by="Score", ascending=False)
            .reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
