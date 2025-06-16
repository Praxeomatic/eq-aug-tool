# tool/services/valuation.py
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

from .aug_stats import load_stats

# ------------------------------------------------------------------
# 1 – default stat weights used if the sidebar sliders are untouched
# ------------------------------------------------------------------
DEFAULT_WEIGHTS: Dict[str, int] = {
    "AC": 1,
    "HP": 1,
    "Mana": 1,
    "Attack": 1,
    "HStr": 1,
    "HSta": 1,
    "HAgi": 1,
    "HDex": 1,
    "HInt": 1,
    "HWis": 1,
}

# optional CSV override if you decide to ship presets
WEIGHTS_CSV = Path(__file__).with_name("default_weights.csv")


def _normalise_id_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the DataFrame has a column named exactly 'ID' (upper-case) so
    downstream merge logic is stable, regardless of whether the parser
    produced 'id', 'Id', or 'item_id'.
    """
    if "ID" in df.columns:
        return df

    for alt in ("id", "Id", "item_id"):
        if alt in df.columns:
            return df.rename(columns={alt: "ID"})

    raise KeyError(
        "Inventory data must contain an ID column "
        "(accepted names: ID, Id, id, item_id). "
        f"Found columns: {list(df.columns)}"
    )


# ------------------------------------------------------------------
# 2 – attach the static augmentation stats to an equipped/unequipped table
# ------------------------------------------------------------------
def attach_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalise_id_column(df)
    stats_df = load_stats()
    return df.merge(stats_df, on="ID", how="left")


# ------------------------------------------------------------------
# 3 – add weighted score columns and a total score
# ------------------------------------------------------------------
def add_item_value(df: pd.DataFrame, weights: Dict[str, int]) -> pd.DataFrame:
    if not weights:  # fall back to defaults if nothing supplied
        weights = DEFAULT_WEIGHTS

    # make sure we have all stat columns; missing ones become zero
    for stat in weights:
        if stat not in df.columns:
            df[stat] = 0

    # per-stat weighted columns
    for stat, w in weights.items():
        df[f"{stat}_w"] = df[stat].fillna(0) * w

    # total score
    weight_cols = [f"{s}_w" for s in weights]
    df["score"] = df[weight_cols].sum(axis=1)

    return df
