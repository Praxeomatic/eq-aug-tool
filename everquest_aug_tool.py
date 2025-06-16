import streamlit as st
import pandas as pd

# === Load scraped augmentation database (includes 'Expansion') ===
@st.cache_data
def load_aug_db():
    df = pd.read_csv("all_augmentations.csv", low_memory=False)
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    return df.set_index("ID")

aug_db = load_aug_db()

# === User stat weights input ===
default_multipliers = {
    "AC": 1, "HP": 1, "Mana": 1, "HSta": 1, "HStr": 1,
    "HAgi": 1, "HDex": 1, "HWis": 1, "HInt": 1,
}

st.sidebar.header("Stat Multipliers")
multipliers = {
    stat: st.sidebar.number_input(stat, value=default)
    for stat, default in default_multipliers.items()
}

# === Compute score for each augment ===
for stat in multipliers:
    col = aug_db[stat] if stat in aug_db.columns else 0
    aug_db[stat] = pd.to_numeric(col, errors="coerce").fillna(0)

def compute_score(row):
    return sum(row[stat] * multipliers[stat] for stat in multipliers)

aug_db["Score"] = aug_db.apply(compute_score, axis=1)

# === Expansion selector ===
expansions = sorted(aug_db["Expansion"].dropna().unique())
selected_expansion = st.selectbox("Select Expansion", expansions)

# === Filter top 15 augs by selected expansion ===
top_15 = aug_db[aug_db["Expansion"] == selected_expansion]
top_15 = top_15.sort_values(by="Score", ascending=False).head(15)

# === Session state for pinned augs ===
if "pinned_augs" not in st.session_state:
    st.session_state["pinned_augs"] = set()

# === Display top 15 augs with pin/unpin buttons ===
st.subheader(f"Top 15 Augmentations in {selected_expansion}")
for _, row in top_15.iterrows():
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"**{row['Name']}** — Score: {row['Score']:.2f}")
    with col2:
        if row.name in st.session_state["pinned_augs"]:
            if st.button("Unpin", key=f"unpin_{row.name}"):
                st.session_state["pinned_augs"].remove(row.name)
        else:
            if st.button("Pin", key=f"pin_{row.name}"):
                st.session_state["pinned_augs"].add(row.name)

# === Display pinned augs ===
if st.session_state["pinned_augs"]:
    st.subheader("📌 Pinned Augmentations (Upgrade Goals)")
    pinned_df = aug_db.loc[aug_db.index.intersection(st.session_state["pinned_augs"])]
    pinned_df = pinned_df.sort_values(by="Score", ascending=False)
    display_cols = ["Name", "Expansion", "Score", "SlotCompat", "FocusEffectName"] + list(multipliers.keys())
    st.dataframe(pinned_df[display_cols].reset_index())
