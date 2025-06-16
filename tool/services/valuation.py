"""
Valuation helpers for the EverQuest Aug Tool.
"""

from __future__ import annotations

import re
from typing import Set

import pandas as pd


# ────────────────────────────────────────────────────────────────────
# Attach stats from the master DB
# ────────────────────────────────────────────────────────────────────
def attach_stats(
    equipped: pd.DataFrame,
    aug_db: pd.DataFrame,
) -> pd.DataFrame:
    equipped = equipped.copy()
    equipped["ID"] = pd.to_numeric(equipped["ID"], errors="coerce").astype("Int64")

    return equipped.merge(
        aug_db, left_on="ID", right_index=True, how="left", sort=False
    )


# ────────────────────────────────────────────────────────────────────
# Weighted ItemValue
# ────────────────────────────────────────────────────────────────────
def add_item_value(
    df: pd.DataFrame,
    multipliers: dict[str, float],
) -> pd.DataFrame:
    df = df.copy()

    for stat in multipliers:
        if stat not in df.columns:
            df[stat] = 0
        df[stat] = pd.to_numeric(df[stat], errors="coerce").fillna(0)

    df["ItemValue"] = df[list(multipliers)].mul(
        pd.Series(multipliers), axis=1
    ).sum(axis=1)
    return df


# ────────────────────────────────────────────────────────────────────
# Ornament detector
# ────────────────────────────────────────────────────────────────────
_ORNAMENT_TYPES = {20, 21, 22}
_ORNAMENT_SLOTS: Set[str] = {"21", "22"}


def _slot_string_to_set(slot_str: str) -> Set[str]:
    """
    Extract numeric tokens from SlotCompat. Accepts '21 22', '21/22', etc.
    """
    return set(re.findall(r"\d+", slot_str))


def is_ornament(row: pd.Series) -> bool:
    """
    True when the augment is purely cosmetic.

    Triggers if ANY of the following are true:
    • AugType is 20, 21, or 22
    • SlotCompat contains only 21/22
    • Name contains the word 'ornament'
    """
    # AugType check
    augtype = row.get("AugType") or row.get("augtype")
    try:
        if int(augtype) in _ORNAMENT_TYPES:
            return True
    except Exception:
        pass

    # SlotCompat check
    slot_set = _slot_string_to_set(str(row.get("SlotCompat", "")))
    if slot_set and slot_set.issubset(_ORNAMENT_SLOTS):
        return True

    # Name keyword
    if "ornament" in str(row.get("Name", "")).lower():
        return True

    return False
