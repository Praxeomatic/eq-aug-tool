# tool/services/aug_stats.py
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Location of the static augmentation stat table
# ---------------------------------------------------------------------
CSV_PATH = Path(__file__).resolve().parent.parent / "all_augmentations.csv"

# Columns exactly as they appear in the CSV
STAT_COLS = [
    "id",
    "ac", "hp", "mana", "attack",
    "heroic_str", "heroic_sta", "heroic_agi",
    "heroic_dex", "heroic_int", "heroic_wis",
]


@st.cache_data(show_spinner=False)
def load_stats() -> pd.DataFrame:
    """
    Read the static augmentation-stats table and return a numeric
    DataFrame indexed by augmentation ID.
    """
    df = pd.read_csv(CSV_PATH, usecols=STAT_COLS)

    # ensure numeric types and fill blanks with zero
    numeric_cols = [c for c in STAT_COLS if c != "id"]
    df[numeric_cols] = (
        df[numeric_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype(int)
    )

    df.set_index("id", inplace=True)
    return df
