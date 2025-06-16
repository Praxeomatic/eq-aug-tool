"""
EverQuest Augmentation Tool – DEV UI
• Left  (BLUE + YELLOW): slot grid & pinned list  (placeholder)
• Center (GREY + GREEN): equipped & unequipped augs
• Right (ORANGE): “Top 15” by era  (placeholder)

Stat-column normalisation lives here, while parsing/valuation is in tool.services.*
"""

from __future__ import annotations

import os
import textwrap
import traceback
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# ──────────────────────────────────────────────────────────────────────────────
# PYTHONPATH safety – add project root
# ──────────────────────────────────────────────────────────────────────────────
import pathlib, sys  # noqa: E402

root = pathlib.Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# ──────────────────────────────────────────────────────────────────────────────
# Local helpers
# ──────────────────────────────────────────────────────────────────────────────
from tool.services.inventory_parser import parse_inventory  # noqa: E402
from tool.services.valuation import attach_stats, add_item_value  # noqa: E402
from tool.ui.purple_weights import render as render_weights  # noqa: E402

# ──────────────────────────────────────────────────────────────────────────────
# Canonical stat names & display order
# ──────────────────────────────────────────────────────────────────────────────
_HEROIC_MAP: Dict[str, List[str]] = {
    "heroic_str": ["HStr", "HSTR", "HeroicSTR"],
    "heroic_sta": ["HSta", "HSTA", "HeroicSTA"],
    "heroic_agi": ["HAgi", "HAGI", "HeroicAGI"],
    "heroic_dex": ["HDex", "HDEX", "HeroicDEX"],
    "heroic_int": ["HInt", "HINT", "HeroicINT"],
    "heroic_wis": ["HWis", "HWIS", "HeroicWIS"],
    "heroic_cha": ["HCha", "HCHA", "HeroicCHA"],
}
_BASE_STATS = ["AC", "HP", "Mana", "Attack"]
_DISPLAY_COLS: List[str] = (
    ["Slot", "Name", "ItemValue"] + _BASE_STATS + list(_HEROIC_MAP.keys())
)

# ──────────────────────────────────────────────────────────────────────────────
# UI utilities
# ──────────────────────────────────────────────────────────────────────────────
def _bar(color: str, label: str) -> None:
    st.markdown(
        f"<div style='background-color:{color};padding:6px;"
        f"border-radius:4px;margin-top:6px;margin-bottom:4px;'>"
        f"<span style='color:#000;font-weight:bold'>{label}</span></div>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Load & normalise augmentation database
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_aug_db(path: str = "augmentation_only_items.csv") -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)

    # ID
    if "ID" not in df.columns:
        for alt in ("id", "Id", "item_id", "ITEMID"):
            if alt in df.columns:
                df.rename(columns={alt: "ID"}, inplace=True)
                break
    if "ID" not in df.columns:
        raise KeyError("CSV is missing an 'ID' column.")

    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")

    # Name
    if "Name" not in df.columns:
        for alt in ("name", "ItemName", "ITEMNAME"):
            if alt in df.columns:
                df.rename(columns={alt: "Name"}, inplace=True)
                break

    # Base-stat aliases
    base_aliases = {
        "AC": ["Ac", "ac", "ACmod"],
        "HP": ["Hp", "hp", "Health"],
        "Mana": ["mana", "MANA"],
        "Attack": ["ATK", "Atk", "AttackMod"],
    }
    for canon, variants in base_aliases.items():
        if canon in df.columns:
            continue
        for alt in variants:
            if alt in df.columns:
                df.rename(columns={alt: canon}, inplace=True)
                break

    # Heroic stat aliases
    for canon, variants in _HEROIC_MAP.items():
        if canon in df.columns:
            continue
        for alt in variants:
            if alt in df.columns:
                df.rename(columns={alt: canon}, inplace=True)
                break

    # Ensure every expected numeric column exists
    numeric_cols = _BASE_STATS + list(_HEROIC_MAP.keys())
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
    df[numeric_cols] = df[numeric_cols].apply(
        pd.to_numeric, errors="coerce"
    ).fillna(0)

    return df.set_index("ID")

# ──────────────────────────────────────────────────────────────────────────────
# Streamlit render
# ──────────────────────────────────────────────────────────────────────────────
def render() -> None:
    cookies = EncryptedCookieManager(prefix="eq-augs/", password=os.getenv("COOKIES_KEY", "debug"))
    aug_db = _load_aug_db()

    # ── Sidebar ────────────────────────────────────
    with st.sidebar:
        _bar("#ff69b4", "Character / Era")
        character = st.text_input("Character name", value="MyWarrior")
        era = st.selectbox("Era", ["Classic", "Kunark", "Velious", "Luclin"])

        _bar("#984ea3", "Stat Weights")
        weights = render_weights(cookies, character)

    # ── RED uploader header across full width ──────
    _bar("#d73027", "Drop character_inventory.txt here")

    # read inventory
    eq_df, un_df = _upload_inventory(weights, aug_db)

    # ── Main three-column layout ───────────────────
    col1, col2, col3 = st.columns([1, 3, 2])

    # Left column (Blue & Yellow placeholders)
    with col1:
        _bar("#4575b4", "Equipped Slots (viewport — TODO)")   # BLUE
        st.write("Placeholder for slot grid")

        _bar("#ffd92f", "Pinned Augs (TODO)")                 # YELLOW
        st.write("Placeholder for pinned list")

    # Middle column (Equipped / Unequipped tables)
    with col2:
        _bar("#9e9e9e", "Equipped Augs")                      # GREY
        _table(eq_df)

        _bar("#4daf4a", "Unequipped Augs")                    # GREEN
        _table(un_df)

    # Right column (Top 15 placeholder)
    with col3:
        _bar("#ff7f00", f"Top 15 Augs — {era} (TODO)")        # ORANGE
        st.write("Placeholder for expansion list")

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _upload_inventory(
    weights: dict[str, float],
    aug_db: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    upload = st.file_uploader("", type="txt", key="inventory_uploader")
    if not upload:
        return pd.DataFrame(), pd.DataFrame()

    try:
        text = upload.read().decode("utf-8", errors="ignore")
        equipped_df = parse_inventory(text)
        if equipped_df.empty:
            st.warning("No augment IDs detected in the uploaded file.")
            return pd.DataFrame(), pd.DataFrame()

        eq_df = attach_stats(equipped_df, aug_db).rename(columns={"EquipSlot": "Slot"})
        eq_df = add_item_value(eq_df, weights)
        eq_df.sort_values("ItemValue", ascending=False, inplace=True)

        return eq_df, pd.DataFrame()   # unequipped not yet implemented

    except Exception as exc:
        st.error("❌ Parser or scoring failed – see details below")
        st.code(textwrap.indent("".join(traceback.format_exception(exc)), "    "))
        return pd.DataFrame(), pd.DataFrame()

def _table(df: pd.DataFrame) -> None:
    if df.empty:
        st.write("No data")
        return
    cols = [c for c in _DISPLAY_COLS if c in df.columns]
    st.dataframe(df[cols].round(2), hide_index=True)
