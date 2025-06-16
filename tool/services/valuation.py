# tool/services/valuation.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

from .aug_stats import load_stats

# ------------------------------------------------------------------
# 1 – default stat weights (slider defaults in the sidebar)
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

# ------------------------------------------------------------------
# 2 – helper: ensure we have a column 'ID' so we can merge on it
# ------------------------------------------------------------------
def _normalise_id_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Guarantee the presence of an 'ID' column (uppercase) regardless of how
    the parser named it. If the DataFrame is empty (no columns at all),
    create an empty 'ID' column so downstream merge logic still works.
    """
    if df.empty and not df.columns.any():
        # empty unequipped list – fabricate empty ID col
        df["ID"] = pd.Series(dtype=int)
        return df

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
# 3 – attach static stats to equipped / unequipped tables
# ------------------------------------------------------------------
def attach_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalise_id_column(df)
    stats_df = load_stats()
    return df.merge(stats_df, on="ID", how="left")

# ------------------------------------------------------------------
# 4 – add weighted score columns and total score
# ------------------------------------------------------------------
def add_item_value(
    df: pd.DataFrame,
    weights: Dict[str, int] | None = None,
) -> pd.DataFrame:
    if weights is None or not weights:
        weights = DEFAULT_WEIGHTS

    # ensure a column exists for every stat
    for stat in weights:
        if stat not in df.columns:
            df[stat] = 0

    # weighted stat columns
    for stat, w in weights.items():
        df[f"{stat}_w"] = df[stat].fillna(0) * w

    # total score
    weight_cols: List[str] = [f"{s}_w" for s in weights]
    df["score"] = df[weight_cols].sum(axis=1)

    return df
