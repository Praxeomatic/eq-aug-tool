"""
inventory_parser.py  –  shared by both branches

parse_inventory_txt(text) →
    Tuple[List[dict], List[dict]]
        • equipped   : rows with ID in master augmentation list and ID != 0
        • unequipped : rows with ID in master augmentation list and ID == 0
"""

from __future__ import annotations

from typing import List, Tuple

from tool.services.aug_stats import load_stats

# ---------------------------------------------------------------------
# Build a set of valid augmentation item-IDs from the stat table
# ---------------------------------------------------------------------
_AUG_IDS = set(load_stats()["ID"])


# ---------------------------------------------------------------------
def parse_inventory_txt(text: str) -> Tuple[List[dict], List[dict]]:
    """
    Parse the /output inventory TSV exported by Raidloot.

    Keeps only rows whose numeric ID exists in _AUG_IDS.
    Splits into:

        equipped   – rows with ID != 0
        unequipped – rows with ID == 0   (empty slots)

    Returns two lists of dicts, each ready to become a DataFrame.
    Dict keys: Location, Name, ID, Slot (if present).
    """
    equipped, unequipped = [], []

    for line in text.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) < 3:
            continue  # malformed row

        loc, name, item_id, *rest = parts

        if item_id.lower() == "id":  # header row
            continue

        try:
            item_id_int = int(item_id)
        except ValueError:
            continue  # non-numeric ID

        if item_id_int not in _AUG_IDS:
            continue  # not an augmentation item

        row = {
            "Location": loc,
            "Name": name,
            "ID": item_id_int,
            "Slot": rest[1] if len(rest) > 1 else "",
        }

        (equipped if item_id_int else unequipped).append(row)

    return equipped, unequipped
