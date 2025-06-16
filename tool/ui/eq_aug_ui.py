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

# Added heroic stats ↓
STAT_ORDER: List[str] = [
    "ItemValue", "AC", "HP", "Mana", "Attack",
    "HStr", "HSta", "HAgi", "HDex", "HInt", "HWis",
]

APP_TITLE = "EverQuest Augmentation Tool — DEV"

# custom colours from your mock-up
KPI_STYLE = """
<style>
.kpi-row       { display:flex; gap:1rem; margin-top:1rem; }
.kpi-box       { flex:1; padding:1rem 0; border-radius:12px; color:white;
                 font-weight:bold; text-align:center; }
.kpi-pink      { background:#d14fb8; }   /* pink box */
.kpi-purple    { background:#673ab7; }   /* purple box */
.kpi-black     { background:#333333; }   /* black box */
.kpi-value     { font-size:1.8rem; line-height:1.2; }
</style>
"""

# ──────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────
def _load_inventory_text(text: str) -> Tuple[list[dict], list[dict]]:
    """
    Parse Raidloot /output inventory TSV export into equipped / unequipped lists.
    Skips header row and ignores non-augmentation items.
    """
    equipped, unequipped = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        loc, name, item_id, *_ = line.split("\t")
        if item_id.lower() == "id":            # header row
            continue
        row = {"Location": loc, "Name": name, "ID": int(item_id)}
        if "(Aug" in name:
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
        st.info(f"*No {label.lower()} augmentations found.*")
        return
    cols = [c for c in STAT_ORDER if c in df.columns]
    st.subheader(label)
    st.dataframe(df[cols], use_container_width=True)


def _render_kpi_boxes(eq_df: pd.DataFrame, un_df: pd.DataFrame):
    """
    Render coloured KPI boxes (pink / purple / black) even before upload.
    """
    total_value = int(eq_df["ItemValue"].sum()) if not eq_df.empty else 0
    upgradable = un_df["Location"].nunique() if not un_df.empty else 0
    unique_augs = eq_df["Name"].nunique() if not eq_df.empty else 0

    st.markdown(KPI_STYLE, unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="kpi-row">
  <div class="kpi-box kpi-pink">
    Total ItemValue<br><span class="kpi-value">{total_value:,}</span>
  </div>
  <div class="kpi-box kpi-purple">
    Upgradable Slots<br><span class="kpi-value">{upgradable}</span>
  </div>
  <div class="kpi-box kpi-black">
    Unique Augs Equipped<br><span class="kpi-value">{unique_augs}</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────
# MAIN RENDER FUNCTION
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

    eq_df = pd.DataFrame()   # placeholders so KPI boxes always show
    un_df = pd.DataFrame()

    if uploaded:
        try:
            text = uploaded.getvalue().decode("utf-8", errors="ignore")
            equipped_raw, unequipped_raw = _load_inventory_text(text)

            eq_df = add_item_value(
                attach_stats(pd.DataFrame(equipped_raw)), weights
            )
            un_df = add_item_value(
                attach_stats(pd.DataFrame(unequipped_raw)), weights
            )

            eq_df.sort_values("ItemValue", ascending=False, inplace=True)
            un_df.sort_values("ItemValue", ascending=False, inplace=True)

            _render_table(eq_df, "Equipped Augments")
            _render_table(un_df, "Unequipped / Empty Slots")

        except Exception as err:
            st.error(f"❌ Parser or scoring failed – {err}")
            st.exception(err)

    # KPI boxes always visible
    _render_kpi_boxes(eq_df, un_df)
