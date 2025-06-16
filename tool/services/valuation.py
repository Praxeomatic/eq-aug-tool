"""
tool.services.valuation
-----------------------
Stat-weighted scoring engine.
"""

from __future__ import annotations
import pandas as pd
from tool.services.aug_stats import load_stats

# List of stat names that must appear both in the weights dict and stats table
STAT_NAMES = [
    "AC", "HP", "Mana", "Attack",
    "HStr", "HSta", "HDex", "HAgi", "HWis", "HInt",
]


def attach_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Merge the stat columns onto the incoming inventory DataFrame."""
    stats_df = load_stats()
    return df.merge(stats_df, on="ID", how="left")


def add_item_value(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """
    Add a numeric `ItemValue` column to *df* using the given weights.
    Any missing stat values are treated as zero.
    """
    for stat in STAT_NAMES:
        w = weights.get(stat, 0.0)
        df[f"{stat}_w"] = df[stat].fillna(0) * w
    df["ItemValue"] = df[[f"{s}_w" for s in STAT_NAMES]].sum(axis=1)
    return df
