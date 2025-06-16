"""
tool.services.aug_stats
-----------------------
Loads `augmentation_only_items.csv`, keeping only the columns we need.
Uses Streamlit's st.cache_data so it loads exactly once per session.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st

# Columns to keep for scoring
STAT_COLS = [
    "ID", "AC", "HP", "Mana", "Attack",
    "HStr", "HSta", "HDex", "HAgi", "HWis", "HInt",
]


@st.cache_data(show_spinner="Loading augmentation stats …")
def load_stats(csv_path: str | Path = "augmentation_only_items.csv") -> pd.DataFrame:
    """
    Return a DataFrame with the stat columns indexed by item ID.

    Raises
    ------
    FileNotFoundError
        If the CSV is not found at the given path.
    """
    df = pd.read_csv(csv_path, usecols=STAT_COLS)
    return df
