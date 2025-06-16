"""
Inventory-file helpers

• parse_inventory(text)               → equipped augments (one per equip slot)
• parse_all_augments(text, aug_db)    → every augment ID in the file,
                                        including those in bags / bank
"""

from __future__ import annotations

import io
import re
from typing import List

import pandas as pd

# canonical equip slots
EQ_SLOTS: List[str] = [
    "Charm", "Ear", "Head", "Face", "Neck", "Shoulders", "Arms", "Back",
    "Wrist", "Range", "Hands", "Primary", "Secondary", "Fingers",
    "Chest", "Legs", "Feet", "Waist", "Ammo",
]

_AUG_SLOT_PREFIX = re.compile(r"^(?P<slot>[^-\t]+)-Slot\d+")


# ────────────────────────────────────────────────────────────────────────
# TSV loader (shared)
# ────────────────────────────────────────────────────────────────────────
def _read_tsv(text: str) -> pd.DataFrame:
    """Return the raw inventory file as a DataFrame."""
    return pd.read_csv(
        io.StringIO(text),
        sep="\t",
        header=0,
        dtype={"Location": str, "Name": str, "ID": "Int64"},
        on_bad_lines="skip",
        engine="python",
    ).fillna({"Location": "", "Name": "", "ID": 0})


# ────────────────────────────────────────────────────────────────────────
# Equipped augments (one per slot)
# ────────────────────────────────────────────────────────────────────────
def parse_inventory(text: str) -> pd.DataFrame:
    df = _read_tsv(text)

    mask = (
        df["Location"].str.contains("-Slot", na=False)
        & (df["Name"].str.casefold() != "empty")
        & (df["ID"] > 0)
    )
    aug_rows = df.loc[mask, ["Location", "ID"]].copy()
    if aug_rows.empty:
        return pd.DataFrame(columns=["EquipSlot", "ID"])

    aug_rows["EquipSlot"] = (
        aug_rows["Location"].str.extract(_AUG_SLOT_PREFIX)["slot"].str.strip()
    )
    aug_rows = aug_rows[aug_rows["EquipSlot"].isin(EQ_SLOTS)]
    return (
        aug_rows[["EquipSlot", "ID"]]
        .drop_duplicates(subset="EquipSlot", keep="first")
        .reset_index(drop=True)
    )


# ────────────────────────────────────────────────────────────────────────
# ALL augments in the file (bags, bank, etc.)
# ────────────────────────────────────────────────────────────────────────
def parse_all_augments(text: str, aug_db: pd.DataFrame) -> pd.DataFrame:
    """
    Return every row whose ID matches an augment in aug_db,
    regardless of where it is located.
    Columns: Location, ID
    """
    df = _read_tsv(text)
    mask = (df["ID"] > 0) & (df["Name"].str.casefold() != "empty")
    df = df.loc[mask, ["Location", "ID"]]

    # inner-join to keep only IDs that exist in the augmentation DB
    df = df.merge(aug_db.reset_index()[["ID"]], on="ID", how="inner")
    return df.reset_index(drop=True)
