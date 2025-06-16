from pathlib import Path
import re

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------
# 1 – CSV location (repo root)
# ---------------------------------------------------------------
CSV_PATH = Path(__file__).resolve().parents[2] / "all_augmentations.csv"

# ---------------------------------------------------------------
# 2 – Canonical stat names and the header variants we accept
# ---------------------------------------------------------------
KEEP_COLS: dict[str, set[str]] = {
    "id": {"id", "ID"},
    "ac": {"ac", "AC"},
    "hp": {"hp", "HP", "hitpoints"},
    "mana": {"mana", "Mana"},
    "attack": {"attack", "Attack", "atk"},
    "heroic_str": {"heroic_str", "HStr", "HSTR", "heroic strength"},
    "heroic_sta": {"heroic_sta", "HSta", "HSTA", "heroic stamina"},
    "heroic_agi": {"heroic_agi", "HAgi", "HAGI", "heroic agility"},
    "heroic_dex": {"heroic_dex", "HDex", "HDEX", "heroic dexterity"},
    "heroic_int": {"heroic_int", "HInt", "HINT", "heroic int"},
    "heroic_wis": {"heroic_wis", "HWis", "HWIS", "heroic wis"},
}

# 2-B legacy aliases expected elsewhere in the codebase
UPPER_ALIAS = {
    "ac": "AC",
    "hp": "HP",
    "mana": "Mana",
    "attack": "Attack",
    "heroic_str": "HStr",
    "heroic_sta": "HSta",
    "heroic_agi": "HAgi",
    "heroic_dex": "HDex",
    "heroic_int": "HInt",
    "heroic_wis": "HWis",
}


def _snake(text: str) -> str:
    """Lower-case and replace non-alphanumeric chars with underscores."""
    return re.sub(r"[^0-9a-z]+", "_", text.lower()).strip("_")


# ---------------------------------------------------------------
# 3 – Cached loader that normalises headers
# ---------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_stats() -> pd.DataFrame:
    """
    Read the augmentation stat table, normalise headers, keep only the
    desired fields, coerce to int. Adds legacy UPPER-CASE aliases so
    old code (`valuation.py`) can merge on 'AC', 'HP', etc.
    """
    raw = pd.read_csv(CSV_PATH)

    # --- map raw headers to canonical names ---------------------------------
    col_map: dict[str, str] = {}
    for canon, variants in KEEP_COLS.items():
        norm_variants = {_snake(v) for v in variants}
        for col in raw.columns:
            if _snake(col) in norm_variants:
                col_map[col] = canon
                break

    missing = [c for c in KEEP_COLS if c not in col_map.values()]
    if missing:
        raise KeyError(
            "CSV is missing expected columns: " + ", ".join(missing)
            + f"\nFound columns: {list(raw.columns)}"
        )

    # --- build tidy DataFrame ----------------------------------------------
    df = (
        raw.rename(columns=col_map)[list(KEEP_COLS)]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype(int)
        .set_index("id")
    )

    # --- add legacy UPPER-CASE aliases for downstream merge logic ----------
    for canon, alias in UPPER_ALIAS.items():
        df[alias] = df[canon]

    # --- expose numeric ID column for merge (valuation expects "ID") -------
    df = df.reset_index().rename(columns={"id": "ID"})
    return df
