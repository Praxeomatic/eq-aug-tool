# tool/services/aug_stats.py
from pathlib import Path
import re

import pandas as pd
import streamlit as st


# ------------------------------------------------------------------
#  CSV lives in the repo root
# ------------------------------------------------------------------
CSV_PATH = Path(__file__).resolve().parents[2] / "all_augmentations.csv"

# Columns we actually care about, in canonical snake-case
KEEP_COLS = {
    # canonical : possible raw header variants
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


def _snake(s: str) -> str:
    """simple header normaliser: lower-case, replace non-alnum with '_'."""
    return re.sub(r"[^0-9a-z]+", "_", s.lower()).strip("_")


@st.cache_data(show_spinner=False)
def load_stats() -> pd.DataFrame:
    """
    Load the static augmentation table, normalise headers, keep only the
    stat columns we care about, coerce to int, return keyed by 'id'.
    """
    raw = pd.read_csv(CSV_PATH)

    # Build a mapping raw_col → canonical_name whenever possible
    col_map = {}
    for canon, variants in KEEP_COLS.items():
        for col in raw.columns:
            if _snake(col) in { _snake(v) for v in variants }:
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

    return df
