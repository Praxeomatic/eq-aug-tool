from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd
import streamlit as st

from tool.services.valuation import (
    attach_stats,
    add_item_value,
    DEFAULT_WEIGHTS,
)

# ──────────────────────────────────────────────────────────────────────
# constants
# ──────────────────────────────────────────────────────────────────────
UPLOAD_TYPES = {"text": ["txt", "tsv"]}

STAT_ORDER = [
    "ItemValue", "AC", "HP", "Mana", "Attack",
    "HStr", "HSta", "HAgi", "HDex", "HInt", "HWis",  # ← heroic stats added
]

APP_TITLE = "EverQuest Augmentation Tool — DEV"

# ──────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────
def _load_inventory_text(text: str) -> Tuple[list[dict], list[dict]]:
    """Parse Raidloot /output inventory TSV into equipped / unequipped lists."""
    equipped, unequipped = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:  # Location, Name, ID, Count, Slots
            continue
        loc, name, item_id, *_ = parts
        row = {"Location": loc, "Name": name, "ID": int(item_id)}
        (equipped if row["ID"] else unequipped).append(row)
    return equipped, unequipped


def _sidebar_weights() -> Dict[str, int]:
    st.sidebar.markdown("### Stat Weights")
    return {
        stat: st.sidebar.number_input(
            stat, min_value=0, max_value=100, value=default, step=1
        )
        for stat, default in DEFAULT_WEIGHTS.items()
    }


def _render_table(df: pd.DataFrame, label: str):
    if df.empty:
        st.info(f"*No {label.lower()} augments found.*")
        return
    cols_in_df = [c for c in STAT_ORDER if c in df.columns]
    st.subheader(label)
    st.dataframe(df[cols_in_df], use_container_width=True)


def _render_kpi_boxes(eq_df: pd.DataFrame, un_df: pd.DataFrame):
    """Show KPI boxes even before a file is uploaded."""
    total_value = int(eq_df["ItemValue"].sum()) if not eq_df.empty else 0
    upgradable = un_df["Location"].nunique() if not un_df.empty else 0

    left, right = st.columns(2)
    with left:
        st.metric("Total ItemValue", f"{total_value:,}")
    with right:
        st.metric("Upgradable Slots", str(upgradable))


# ──────────────────────────────────────────────────────────────────────
# main render function
# ──────────────────────────────────────────────────────────────────────
def render():
    st.title(APP_TITLE)

    # sidebar
    weights = _sidebar_weights()
    st.sidebar.markdown("### Upload inventory.txt")

    uploaded = st.sidebar.file_uploader(
        "Drag the Raidloot export here ↴",
        type=UPLOAD_TYPES["text"],
        accept_multiple_files=False,
    )

    # placeholders so KPI boxes always render
    eq_df = pd.DataFrame()
    un_df = pd.DataFrame()

    if uploaded:
        try:
            text = uploaded.getvalue().decode("utf-8", errors="ignore")
            equipped_raw, unequipped_raw = _load_inventory_text(text)

            eq_df = add_item_value(attach_stats(pd.DataFrame(equipped_raw)), weights)
            un_df = add_item_value(attach_stats(pd.DataFrame(unequipped_raw)), weights)

            eq_df.sort_values("ItemValue", ascending=False, inplace=True)
            un_df.sort_values("ItemValue", ascending=False, inplace=True)

            _render_table(eq_df, "Equipped Augments")
            _render_table(un_df, "Unequipped / Empty Slots")

        except Exception as err:
            st.error(f"❌ Parser or scoring failed – {err}")
            st.exception(err)

    # KPI boxes always visible
    _render_kpi_boxes(eq_df, un_df)
