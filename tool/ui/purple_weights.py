"""
Stat Weights editor (PURPLE box).
Stores presets in a cookie keyed by character name.
"""
from __future__ import annotations
import json
from typing import Dict

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

STAT_NAMES = [
    "AC", "HP", "Mana", "Attack",
    "HStr", "HSta", "HDex", "HAgi", "HWis", "HInt",
]
DEFAULT_WEIGHTS = {s: 1.0 for s in STAT_NAMES}


def _cookie_key(char: str) -> str:
    return f"weights::{char}"


def _load(cookies: EncryptedCookieManager, char: str) -> Dict[str, Dict[str, float]]:
    raw = cookies.get(_cookie_key(char))
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return {"Default": DEFAULT_WEIGHTS.copy()}


def _save(cookies: EncryptedCookieManager, char: str, presets: dict) -> None:
    cookies[_cookie_key(char)] = json.dumps(presets)
    cookies.save()


def render(cookies: EncryptedCookieManager, character: str) -> Dict[str, float]:
    presets = _load(cookies, character)

    st.subheader("Stat Weights")

    preset_names = list(presets.keys())
    selected = st.selectbox("Preset", preset_names, key=f"{character}_preset")

    working = st.session_state.setdefault(
        f"{character}_weights", presets[selected].copy()
    )

    # numeric inputs
    col1, col2 = st.columns(2)
    for idx, stat in enumerate(STAT_NAMES):
        col = col1 if idx % 2 == 0 else col2
        working[stat] = col.number_input(
            stat, value=working[stat], step=0.1, key=f"{character}_{stat}"
        )

    preset_name = st.text_input("Preset name", value=selected, key=f"{character}_name")
    save_col, del_col = st.columns(2)
    with save_col:
        if st.button("Save", key=f"{character}_save"):
            presets[preset_name] = working.copy()
            _save(cookies, character, presets)
            st.success(f"Saved '{preset_name}'")
    with del_col:
        if st.button("Delete", key=f"{character}_del") and preset_name in presets:
            del presets[preset_name]
            _save(cookies, character, presets)
            st.warning(f"Deleted '{preset_name}'")
            st.experimental_rerun()

    return working
