from __future__ import annotations

from typing import Dict, Tuple, List

import pandas as pd
import streamlit as st

from tool.services.valuation import (
    attach_stats,
    add_item_value,
    DEFAULT_WEIGHTS,
)

# ──────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────
UPLOAD_TYPES = {"text": ["txt", "tsv"]}

STAT_ORDER = [
    "ItemValue", "AC", "HP", "Mana", "Attack",
    "HStr", "HSta", "HAgi", "HDex", "HInt", "HWis",
]

APP_TITLE = "EverQuest Augmentation Tool — DEV"

KPI_STYLE = """
<style>
.kpi-box {
  padding: 1rem;
  border-radius: 0.75rem;
  color: white;
  font-weight: bold;
  text-align: center;
}
.kpi-green { background: #2d8659; }
.kpi-blue  { background: #3076d1; }
</style>
"""

# ──────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────
def _load_inventory_text(text: str) -> Tuple[List[dict], List[dict]]:
    """
    Parse Raidloot /output inventory TSV export.
    Returns lists of dicts for equipped augs and unequipped slots.
    Rows whose ID is zero or whose name does NOT contain "(Aug)" are ignored.
    """
    equipped, unequipped = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:  # Location, Name, ID, Count, Slots
            continue

        loc, name, item_id, *_ = parts
        if item_id.lower() == "id":       # header row
            continue

        row = {"Location": loc, "Name": name, "ID": int(item_id)}
        if "(Aug" in name:                # augmentation rows only
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
        st.info(f"*No {label.lower()} augmentation rows found.*")
        return
    cols_in_df = [c for c in STAT_ORDER if c in df.columns]
    st.subheader(label)
    st.dataframe(df[cols_in_df], use_container_width=True)


def _render_kpi_boxes(eq_df: pd.DataFrame, un_df: pd.DataFrame):
    """
    Colored KPI boxes always visible.  Uses same style as original mock-up.
    """
    total_value = int(eq_df["ItemValue"].sum()) if not eq_df.empty else 0
    upgradable = un_df["Location"].nunique() if not un_df.empty else 0

    st.markdown(KPI_STYLE, unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f'<div class="kpi-box kpi-green">Total ItemValue<br><span style="font-size:1.5rem">{total_value:,}</span></div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'<div class="kpi-box kpi-blue">Upgradable Slots<br><span style="font-size:1.5rem">{upgradable}</span></div>',
            unsafe_allow_html=True,
        )

# ──────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────
def render():
    st.title(APP_TITLE)

    weights = _sidebar_weights()
    st.sidebar.markdown("### Upload inventory.txt")

    uploaded = st.sidebar.file_uploader(
        "Drag the Raidloot export here ↴",
        type=UPLOAD_TYPES["text"],
        accept_multiple_files=False,
    )

    eq_df = pd.DataFrame()   # placeholders for KPI boxes
    un_df = pd.DataFrame()

    if uploaded:
        try:
            text = uploaded.getvalue().decode("utf-8", errors="ignore")
            equipped_raw, unequipped_raw = _load_inventory_text(text)

            # merge with stat table (suffixes prevents Name_x/Name_y)
            eq_df = add_item_value(
                attach_stats(pd.DataFrame(equipped_raw)),
                weights,
            )
            un_df = add_item_value(
                attach_stats(pd.DataFrame(unequipped_raw)),
                weights,
            )

            eq_df.sort_values("ItemValue", ascending=False, inplace=True)
            un_df.sort_values("ItemValue", ascending=False, inplace=True)

            _render_table(eq_df, "Equipped Augments")
            _render_table(un_df, "Unequipped / Empty Slots")

        except Exception as err:
            st.error(f"❌ Parser or scoring failed – {err}")
            st.exception(err)

    # KPI boxes always on screen
    _render_kpi_boxes(eq_df, un_df)
