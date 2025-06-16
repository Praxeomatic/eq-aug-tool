from pathlib import Path
import re

import pandas as pd
import streamlit as st

# ------------------------------------------------------------------
# CSV lives in the repository root
# ------------------------------------------------------------------
CSV_PATH = Path(__file__).resolve().parents[2] / "all_augmentations.csv"

# Canonical column names and the variants that may appear in the CSV
KEEP_COLS = {
    "id":          {"id", "ID"},
    "ac":          {"ac", "AC"},
    "hp":          {"hp", "HP", "hitpoints"},
    "mana":        {"mana", "Mana"},
    "attack":      {"attack", "Attack", "atk"},
    "heroic_str":  {"heroic_str", "HStr", "HSTR", "heroic strength"},
    "heroic_sta":  {"heroic_sta", "HSta", "HSTA", "heroic stamina"},
    "heroic_agi":  {"heroic_agi", "HAgi", "HAGI", "heroic agility"},
    "heroic_dex":  {"heroic_dex", "HDex", "HDEX", "heroic dexterity"},
    "heroic_int":  {"heroic_int", "HInt", "HINT", "heroic int"},
    "heroic_wis":  {"heroic_wis", "HWis", "HWIS", "heroic wis"},
}


def _snake(text: str) -> str:
    """Lower-case and replace non-alphanumeric with underscores."""
    return re.sub(r"[^0-9a-z]+", "_", text.lower()).strip("_")


@st.cache_data(show_spinner=False)
def load_stats() -> pd.DataFrame:
    """
    Load the augmentation stat table, normalise headers, keep only wanted
    columns, coerce to int, and return a DataFrame keyed by 'ID'.
    """
    raw = pd.read_csv(CSV_PATH)

    # Map raw headers to canonical names
    col_map: dict[str, str] = {}
    for canon, variants in KEEP_COLS.items():
        normalized_variants = {_snake(v) for v in variants}
        for col in raw.columns:
            if _snake(col) in normalized_variants:
                col_map[col] = canon
                break

    missing = [c for c in KEEP_COLS if c not in col_map.values()]
    if missing:
        raise KeyError(
            f"CSV is missing expected columns: {', '.join(missing)}\n"
            f"Found columns: {list(raw.columns)}"
        )

    df = (
        raw.rename(columns=col_map)[list(KEEP_COLS)]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype(int)
        .set_index("id")
    )

    # expose the numeric ID column for downstream merge logic
    df = df.reset_index().rename(columns={"id": "ID"})
    return df
