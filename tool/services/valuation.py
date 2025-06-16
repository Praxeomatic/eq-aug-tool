# tool/services/valuation.py
from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

from .aug_stats import load_stats

# ------------------------------------------------------------------
# 1 – default stat weights (sidebar sliders)
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
# 2 – helper: ensure column 'ID' exists
# ------------------------------------------------------------------
def _normalise_id_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty and not df.columns.any():
        df["ID"] = pd.Series(dtype=int)
        return df

    if "ID" in df.columns:
        return df

    for alt in ("id", "Id", "item_id"):
        if alt in df.columns:
            return df.rename(columns={alt: "ID"})

    raise KeyError(
        "Inventory data must contain an ID column "
        "(accepted: ID, Id, id, item_id). "
        f"Found columns: {list(df.columns)}"
    )

# ------------------------------------------------------------------
# 3 – merge static stats
# ------------------------------------------------------------------
def attach_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalise_id_column(df)
    stats_df = load_stats()
    return df.merge(stats_df, on="ID", how="left")

# ------------------------------------------------------------------
# 4 – add weighted values and total
# ------------------------------------------------------------------
def add_item_value(
    df: pd.DataFrame,
    weights: Dict[str, int] | None = None,
) -> pd.DataFrame:
    if not weights:
        weights = DEFAULT_WEIGHTS

    # ensure every weighted stat column exists
    for stat in weights:
        if stat not in df.columns:
            df[stat] = 0

    # weighted stat columns
    for stat, w in weights.items():
        df[f"{stat}_w"] = df[stat].fillna(0) * w

    # total value
    weight_cols: List[str] = [f"{s}_w" for s in weights]
    df["score"] = df[weight_cols].sum(axis=1)

    # alias expected by UI
    df["ItemValue"] = df["score"]

    return df
