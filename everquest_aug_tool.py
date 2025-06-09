import streamlit as st
import pandas as pd

# === Valid Gear Slot Prefixes ===
VALID_SLOT_PREFIXES = {
    "Charm", "Ear", "Head", "Face", "Neck", "Shoulders", "Arms", "Back",
    "Wrist", "Range", "Hands", "Primary", "Secondary", "Finger",
    "Chest", "Legs", "Feet", "Waist", "Power Source"
}

MULTISLOT_TYPES = {"Ear", "Finger", "Wrist"}

# === Stat Mapping ===
STAT_MAP = {
    "ac": "AC",
    "hp": "HP",
    "mana": "Mana",
    "heroic_str": "HStr",
    "heroic_sta": "HSta",
    "heroic_agi": "HAgi",
    "heroic_dex": "HDex",
    "heroic_wis": "HWis",
    "heroic_int": "HInt",
}
BACKEND_STATS = list(STAT_MAP.keys())
UI_STATS = list(STAT_MAP.values())

# === Load Database (excludes ornaments) ===
@st.cache_data
def load_aug_db():
    df = pd.read_csv("augmentation_only_items.csv", low_memory=False)
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.set_index("id")
    df = df[df["charmfile"].isna() | (df["charmfile"].str.strip() == "")]
    return df

aug_db = load_aug_db()

available_stats = [s for s in BACKEND_STATS if s in aug_db.columns]
available_ui = [STAT_MAP[s] for s in available_stats]
backend_from_ui = {v: k for k, v in STAT_MAP.items() if k in available_stats}

# === Sidebar: Stat Weights ===
st.sidebar.header("Stat Multipliers")
multipliers = {ui: st.sidebar.number_input(ui, value=1.0) for ui in available_ui}

# === Upload Section ===
st.title("Prax Mke ur Augs Gudder with Python AI Slop Webapp")
uploaded_file = st.file_uploader("Upload your EverQuest `/output inventory` .txt file", type="txt")

# === Inventory Parser ===
def parse_augments(file):
    lines = file.getvalue().decode("utf-8").splitlines()
    aug_rows = []
    for line in lines:
        parts = line.strip().split("\t")
        if len(parts) != 5:
            continue
        location, name, item_id, count, slots = parts
        if "Slot" in location and name != "Empty" and item_id != "0":
            slot_parts = location.split("-")
            slot_prefix = slot_parts[0]
            display_slot = location if slot_prefix in MULTISLOT_TYPES else slot_prefix
            is_equipped = slot_prefix in VALID_SLOT_PREFIXES
            aug_rows.append({
                "Slot": display_slot,
                "SlotPrefix": slot_prefix,
                "Name": name,
                "ID": int(item_id),
                "Equipped": is_equipped
            })
    return pd.DataFrame(aug_rows)

# === Scoring Function ===
def compute_score(row):
    return sum(row.get(backend_from_ui[ui], 0) * multipliers[ui] for ui in available_ui)

# === Main Logic ===
if uploaded_file:
    parsed = parse_augments(uploaded_file)
    parsed = parsed[parsed["ID"].isin(aug_db.index)]
    merged = parsed.merge(aug_db, how="left", left_on="ID", right_index=True)

    for stat in available_stats:
        merged[stat] = pd.to_numeric(merged[stat], errors="coerce").fillna(0)

    merged["Score"] = merged.apply(compute_score, axis=1)
    merged["Focus Effect"] = merged.get("focusname", "").fillna("")

    display_cols = ["Slot", "Name", "Score"] + available_stats + ["Focus Effect"]
    display_renamed = ["Slot", "Name", "Score"] + [STAT_MAP[c] for c in available_stats] + ["Focus Effect"]

    # === Equipped Augs ===
    equipped_df = merged[merged["Equipped"] == True].copy()
    equipped_df = equipped_df[display_cols]
    equipped_df.columns = display_renamed
    equipped_df = equipped_df.sort_values("Score", ascending=False)

    st.subheader("Equipped Augs")
    st.dataframe(
        equipped_df.style.format({
            **{ui: lambda v: "" if v == 0 else v for ui in available_ui},
            "Score": "{:.1f}"
        }),
        hide_index=True,
        use_container_width=True
    )

    # === Unequipped Augs (from inventory only) ===
    unequipped_df = merged[merged["Equipped"] == False].copy()
    unequipped_df["Score"] = unequipped_df.apply(compute_score, axis=1)
    unequipped_df["Focus Effect"] = unequipped_df.get("focusname", "").fillna("")
    if "Name" not in unequipped_df.columns and "name" in unequipped_df.columns:
        unequipped_df["Name"] = unequipped_df["name"]
    unequipped_df["Slot"] = unequipped_df["Slot"]

    unequipped_df = unequipped_df[display_cols]
    unequipped_df.columns = display_renamed
    unequipped_df = unequipped_df.sort_values("Score", ascending=False)

    st.subheader("Unequipped Augmentations (Scored)")
    st.dataframe(
        unequipped_df.style.format({
            **{ui: lambda v: "" if v == 0 else v for ui in available_ui},
            "Score": "{:.1f}"
        }),
        hide_index=True,
        use_container_width=True
    )
