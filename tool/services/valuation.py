"""Augmentation valuation & filtering logic."""

from __future__ import annotations

from typing import Dict

import pandas as pd
import streamlit as st

from .aug_stats import load_stats

# ------------------------------------------------------------------
# Static weights
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

AUG_IDS = set(load_stats()["ID"])

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _filter_augs(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows whose ID is a valid augmentation."""
    if df.empty or "ID" not in df.columns:         # ← guard for empty input
        return df.copy()
    return df[df["ID"].isin(AUG_IDS)].copy()


def attach_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Merge inventory rows with static augmentation stats."""
    df = _filter_augs(df)
    if df.empty:
        return df
    stats_df = load_stats()
    return df.merge(stats_df, on="ID", how="left")


def add_item_value(df: pd.DataFrame, weights: Dict[str, int]) -> pd.DataFrame:
    """Add per-stat weighted columns and total ItemValue score."""
    if df.empty:
        return df

    if not weights:
        weights = DEFAULT_WEIGHTS

    for stat in weights:
        if stat not in df.columns:
            df[stat] = 0

    for stat, w in weights.items():
        df[f"{stat}_w"] = df[stat].fillna(0) * w

    weight_cols = [f"{s}_w" for s in weights]
    df["ItemValue"] = df[weight_cols].sum(axis=1)
    return df
