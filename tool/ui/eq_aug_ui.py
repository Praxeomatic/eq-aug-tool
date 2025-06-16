"""
UI layer for the EverQuest Augmentation Tool.
Handles layout only; scoring lives in tool.services.*
"""

from __future__ import annotations

import os
import textwrap
import traceback
from typing import Tuple

import pandas as pd
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from tool.models.inventory_parser import parse_inventory_txt
from tool.ui.purple_weights import render as render_weights
from tool.services.valuation import attach_stats, add_item_value


# ---------------------------------------------------------------------
# Helper to draw coloured header bars (matches mock-up)
# ---------------------------------------------------------------------
def _bar(color: str, label: str) -> None:
    st.markdown(
        f"<div style='background-color:{color};"
        f"padding:6px;border-radius:4px;margin-top:6px;margin-bottom:4px;'>"
        f"<span style='color:#000;font-weight:bold'>{label}</span></div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# MAIN RENDER FUNCTION  –  called every Streamlit rerun
# ---------------------------------------------------------------------
def render() -> None:
    cookies = EncryptedCookieManager(
        prefix="eq-augs/", password=os.getenv("COOKIES_KEY", "debug")
    )

    # ----- sidebar (PINK + PURPLE) -----------------------------------
    with st.sidebar:
        _bar("#ff69b4", "Character / Era")          # PINK
        character = st.text_input("Character name", value="MyWarrior")
        era = st.selectbox("Era", ["Classic", "Kunark", "Velious", "Luclin"])

        _bar("#984ea3", "Stat Weights")             # PURPLE
        weights = render_weights(cookies, character)

    # ----- RED  inventory uploader ----------------------------------
    _bar("#d73027", "Drop character_inventory.txt here")  # RED
    eq_df, un_df = _upload_inventory(weights)

    # ----- layout ----------------------------------------------------
    col1, col2, col3 = st.columns([1, 3, 2])

    with col1:
        _bar("#4575b4", "Equipped Slots (viewport — TODO)")   # BLUE
        st.write("Placeholder for slot grid")

        _bar("#ffd92f", "Pinned Augs (TODO)")                 # YELLOW
        st.write("Placeholder for pinned list")

    with col2:
        _bar("#9e9e9e", "Equipped Augs")                      # GREY
        _table(eq_df)

        _bar("#4daf4a", "Unequipped Augs")                    # GREEN
        _table(un_df)

    with col3:
        _bar("#ff7f00", f"Top 15 Augs — {era} (TODO)")        # ORANGE
        st.write("Placeholder for expansion list")


# ---------------------------------------------------------------------
# RED zone helpers
# ---------------------------------------------------------------------
def _upload_inventory(weights: dict[str, float]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    upload = st.file_uploader("", type="txt", key="inventory_uploader")
    if not upload:
        return pd.DataFrame(), pd.DataFrame()

    try:
        text = upload.read().decode("utf-8", errors="ignore")
        equipped, unequipped = parse_inventory_txt(text)

        # Merge stats and compute ItemValue
        eq_df = add_item_value(attach_stats(pd.DataFrame(equipped)), weights)
        un_df = add_item_value(attach_stats(pd.DataFrame(unequipped)), weights)

        # Sort tables by ItemValue descending
        eq_df.sort_values("ItemValue", ascending=False, inplace=True)
        un_df.sort_values("ItemValue", ascending=False, inplace=True)

        return eq_df, un_df

    except Exception as exc:
        st.error("❌ Parser or scoring failed – see details below")
        st.code(textwrap.indent("".join(traceback.format_exception(exc)), "    "))
        return pd.DataFrame(), pd.DataFrame()


# ---------------------------------------------------------------------
# Generic table renderer
# ---------------------------------------------------------------------
def _table(df: pd.DataFrame) -> None:
    if df.empty:
        st.write("No data")
    else:
        st.dataframe(
            df[["Slot", "Name", "ItemValue", "AC", "HP", "Mana", "Attack"]].round(2),
            hide_index=True,
        )
