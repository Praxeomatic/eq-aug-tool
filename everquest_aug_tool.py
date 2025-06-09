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

def extract_all_augs_from_inventory(txt_file):
    aug_rows = []
    lines = txt_file.getvalue().decode("utf-8").splitlines()
    for line in lines:
        parts = line.strip().split("\t")
        if len(parts) != 5:
            continue
        location, name, item_id, count, slots = parts
        if "-Slot" in location and name != "Empty" and item_id != "0":
            try:
                item_id_int = int(item_id)
                if item_id_int in aug_db.index:
                    aug_rows.append({
                        "ID": item_id_int,
                        "Name": name,
                        "Location": location
                    })
            except ValueError:
                continue
    return pd.DataFrame(aug_rows)

def compute_score(row, multipliers):
    return sum(row[stat] * multipliers[stat] for stat in multipliers)

if uploaded_file:
    equipped_df = extract_augs_from_inventory(uploaded_file)
    all_augs_df = extract_all_augs_from_inventory(uploaded_file)

    if equipped_df.empty and all_augs_df.empty:
        st.error("No augmentations found in this file.")
    else:
        equipped_df = equipped_df[equipped_df["ID"].isin(aug_db.index)]
        merged_eq = equipped_df.merge(aug_db, how="inner", left_on="ID", right_index=True)

        for stat in default_multipliers:
            if stat in merged_eq.columns:
                merged_eq[stat] = pd.to_numeric(merged_eq[stat], errors="coerce").fillna(0)
            else:
                merged_eq[stat] = 0

        merged_eq["Score"] = merged_eq.apply(lambda row: compute_score(row, multipliers), axis=1)
        merged_eq["FocusEffect"] = merged_eq.get("focusname", "")

        st.subheader("Equipped Augmentations (Scored)")
        display_cols = ["ParentSlot", "Name", "ID", "Score"] + list(default_multipliers.keys()) + ["FocusEffect"]
        styled_eq = merged_eq[display_cols].sort_values(by="Score", ascending=False).reset_index(drop=True)
        styled_eq = styled_eq.style.format({stat: lambda x: "" if x == 0 else int(x) for stat in default_multipliers})
        st.dataframe(styled_eq, use_container_width=True, hide_index=True)

        # Show unequipped augs: all - equipped
        if not all_augs_df.empty:
            equipped_ids = set(equipped_df["ID"])
            unequipped_df = all_augs_df[~all_augs_df["ID"].isin(equipped_ids)]
            merged_uneq = unequipped_df.merge(aug_db, how="inner", left_on="ID", right_index=True)

            for stat in default_multipliers:
                if stat in merged_uneq.columns:
                    merged_uneq[stat] = pd.to_numeric(merged_uneq[stat], errors="coerce").fillna(0)
                else:
                    merged_uneq[stat] = 0

            merged_uneq["Score"] = merged_uneq.apply(lambda row: compute_score(row, multipliers), axis=1)
            merged_uneq["FocusEffect"] = merged_uneq.get("focusname", "")

            st.subheader("Unequipped Augmentations (Scored)")
            display_cols_uneq = ["Location", "Name", "ID", "Score"] + list(default_multipliers.keys()) + ["FocusEffect"]
            styled_uneq = merged_uneq[display_cols_uneq].sort_values(by="Score", ascending=False).reset_index(drop=True)
            styled_uneq = styled_uneq.style.format({stat: lambda x: "" if x == 0 else int(x) for stat in default_multipliers})
            st.dataframe(styled_uneq, use_container_width=True, hide_index=True)
