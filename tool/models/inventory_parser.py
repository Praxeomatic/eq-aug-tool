"""
Light-weight parser for EverQuest `/output inventory` text files.

Returns two lists of dicts:
    • equipped  – augment rows actually slotted into gear (Location contains “-Slot” and ID ≠ 0)
    • unequipped – augment-like items that are not currently slotted

This version is intentionally simple; improve the heuristics as needed.
"""

from __future__ import annotations
import csv, io, re
from typing import List, Dict, Tuple


AUG_NAME_PATTERN = re.compile(r"(shard|stone|augment|aug|gem)", re.I)


def _find_header_index(lines: list[str]) -> int | None:
    """Return the index where the 'Location\tName\tID' header line occurs."""
    for i, ln in enumerate(lines):
        if ln.lower().startswith("location\tname\tid"):
            return i
    return None


def parse_inventory_txt(text: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse the TSV inventory dump.

    Parameters
    ----------
    text : str
        Raw text from the `/output inventory` file.

    Returns
    -------
    equipped : list[dict]
    unequipped : list[dict]
    """
    equipped: list[dict] = []
    unequipped: list[dict] = []

    lines = text.splitlines()
    header_idx = _find_header_index(lines)
    if header_idx is None:
        # No header found – return empty results
        return equipped, unequipped

    reader = csv.reader(io.StringIO("\n".join(lines[header_idx:])), delimiter="\t")
    header = next(reader, None)
    if not header or header[:3] != ["Location", "Name", "ID"]:
        return equipped, unequipped  # malformed header

    for row in reader:
        if len(row) < 3:
            continue
        location, name, id_raw = row[:3]

        try:
            aug_id = int(id_raw)
        except ValueError:
            continue  # skip rows with non-numeric IDs

        count = int(row[3]) if len(row) > 3 and row[3].isdigit() else 0

        # ----- classify ------------------------------------------------------
        if "-Slot" in location and aug_id != 0:
            # Example Location: "Ear-Slot1"
            slot_root = location.split("-")[0]  # Ear, Head, Fingers, …
            equipped.append(
                {
                    "Slot": slot_root,
                    "Location": location,
                    "Name": name,
                    "ID": aug_id,
                    "Count": count,
                }
            )
        else:
            # crude heuristic: treat as augment if name looks like one
            if aug_id != 0 and AUG_NAME_PATTERN.search(name):
                unequipped.append(
                    {
                        "Container": location,
                        "Name": name,
                        "ID": aug_id,
                        "Count": count,
                    }
                )

    return equipped, unequipped
