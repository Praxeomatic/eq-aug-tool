"""
Valuation helpers for the EverQuest Aug Tool.

• attach_stats()  – left-join equipped augment IDs to the master database
• add_item_value() – compute weighted ItemValue using user multipliers
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------
# Join equipped IDs to the augmentation database
# ---------------------------------------------------------------------
def attach_stats(
    equipped: pd.DataFrame,
    aug_db: pd.DataFrame,
) -> pd.DataFrame:
    """
    Parameters
    ----------
    equipped : DataFrame
        Columns: EquipSlot, ID (integer)
    aug_db : DataFrame
        Master aug database **indexed by ID** (see _load_aug_db).

    Returns
    -------
    DataFrame
        All columns from `equipped` plus the stat columns from `aug_db`.
    """
    equipped = equipped.copy()
    equipped["ID"] = pd.to_numeric(equipped["ID"], errors="coerce").astype("Int64")

    # aug_db has ID as its index → merge on right_index
    merged = equipped.merge(
        aug_db, left_on="ID", right_index=True, how="left", sort=False
    )
    return merged


# ---------------------------------------------------------------------
# Compute ItemValue column
# ---------------------------------------------------------------------
def add_item_value(
    df: pd.DataFrame,
    multipliers: dict[str, float],
) -> pd.DataFrame:
    """
    Adds / replaces the 'ItemValue' column using user-supplied weights.

    multipliers example:
        {"heroic_wis": 35, "HP": 1, "Mana": 1, "AC": 1}
    """
    df = df.copy()

    # ensure every stat column exists and is numeric
    for stat, weight in multipliers.items():
        if stat not in df.columns:
            df[stat] = 0
        df[stat] = pd.to_numeric(df[stat], errors="coerce").fillna(0)

    # vectorised dot-product
    df["ItemValue"] = df[list(multipliers.keys())].mul(
        pd.Series(multipliers), axis=1
    ).sum(axis=1)

    return df
