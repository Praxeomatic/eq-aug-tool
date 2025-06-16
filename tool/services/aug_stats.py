# tool/services/aug_stats.py
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# CSV lives in the **repo root** (three levels up from this file)
# ---------------------------------------------------------------------
CSV_PATH = Path(__file__).resolve().parents[2] / "all_augmentations.csv"

# Column names exactly as they appear in all_augmentations.csv
STAT_COLS = [
    "id",
    "ac", "hp", "mana", "attack",
    "heroic_str", "heroic_sta", "heroic_agi",
    "heroic_dex", "heroic_int", "heroic_wis",
]

@st.cache_data(show_spinner=False)
def load_stats() -> pd.DataFrame:
    """Load the static augmentation-stats table and return a numeric DataFrame indexed by ID."""
    df = pd.read_csv(CSV_PATH, usecols=STAT_COLS)

    numeric_cols = [c for c in STAT_COLS if c != "id"]
    df[numeric_cols] = (
        df[numeric_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype(int)
    )

    return df.set_index("id")
