"""
Parse EverQuest `/output inventory` files produced in *tab-separated* format.

The game outputs five columns with a header row:

    Location<Name>ID<Count><Slots>

Key facts for augment detection
-------------------------------
• Rows whose **Location** field contains “-Slot” hold *either* an augment
  or an empty slot filler.

• An augment row always has
      • Location like “Head-Slot1”, “Charm-Slot2”, …
      • Name  ≠ “Empty”
      • ID    > 0

• The equipment slot we care about is the part *before* the first “-”,
  e.g. “Head-Slot2” → “Head”.

The parser returns one row per augment with columns
    EquipSlot   canonical slot name (Ear, Head, …)
    ID          integer item ID of the augment
"""

from __future__ import annotations

import io
import re
from typing import List

import pandas as pd

# canonical EverQuest equipment slots
EQ_SLOTS: List[str] = [
    "Charm",
    "Ear",
    "Head",
    "Face",
    "Neck",
    "Shoulders",
    "Arms",
    "Back",
    "Wrist",
    "Range",
    "Hands",
    "Primary",
    "Secondary",
    "Fingers",
    "Chest",
    "Legs",
    "Feet",
    "Waist",
    "Ammo",
]

# compile once
_SLOT_PREFIX = re.compile(r"^(?P<slot>[^-\t]+)-Slot\d+")


def _read_tsv(text: str) -> pd.DataFrame:
    """Load the tab-separated inventory text into a DataFrame."""
    # Some files have Windows CRLF and blank lines; pandas handles both.
    return pd.read_csv(
        io.StringIO(text),
        sep="\t",
        header=0,
        dtype={"Location": str, "Name": str, "ID": "Int64"},
        on_bad_lines="skip",
        engine="python",
    ).fillna({"Location": "", "Name": "", "ID": 0})


def parse_inventory(text: str) -> pd.DataFrame:
    """
    Extract augments currently equipped.

    Returns a DataFrame with columns: EquipSlot, ID
    """
    df = _read_tsv(text)

    # keep only rows like "Head-Slot1", "Charm-Slot2", etc.
    mask_aug_row = (
        df["Location"].str.contains("-Slot", na=False)
        & (df["Name"].str.casefold() != "empty")
        & (df["ID"] > 0)
    )
    aug_rows = df.loc[mask_aug_row, ["Location", "ID"]].copy()

    if aug_rows.empty:
        return pd.DataFrame(columns=["EquipSlot", "ID"])

    # Extract the equipment slot prefix
    aug_rows["EquipSlot"] = (
        aug_rows["Location"]
        .str.extract(_SLOT_PREFIX)["slot"]
        .str.strip()
    )

    # Normalise: EverQuest uses singular (“Fingers”) vs our EQ_SLOTS list
    # All inventory prefixes already match the EQ_SLOTS capitalisation.

    # Drop rows whose slot is not in the canonical list (guards against bags,
    # bank slots, etc.)
    aug_rows = aug_rows[aug_rows["EquipSlot"].isin(EQ_SLOTS)]

    # One augment per equipment slot – keep first occurrence
    result = (
        aug_rows[["EquipSlot", "ID"]]
        .drop_duplicates(subset="EquipSlot", keep="first")
        .reset_index(drop=True)
    )

    return result
