# tool/ui/eq_aug_ui.py
from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd
import streamlit as st

from tool.services.valuation import (
    attach_stats,
    add_item_value,
    DEFAULT_WEIGHTS,
)

# ----------------------------------------------------------------------
# constants
# ----------------------------------------------------------------------
UPLOAD_TYPES = {"text": ["txt", "tsv"]}
STAT_ORDER = [
    "ItemValue", "AC", "HP", "Mana", "Attack",
    "HStr", "HSta", "HAgi", "HDex", "HInt", "HWis",
]
APP_TITLE = "EverQuest Augmentation Tool — DEV"

# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def _load_inventory_text(text: str) -> Tuple[list[dict], list[dict]]:
    equipped, unequipped = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        loc, name, item_id, *_ = parts
        row = {"Location": loc, "Name": name, "ID": int(item_id)}
        (equipped if row["ID"] else unequipped).append(row)
    return equipped, unequipped


def _sidebar_weights() -> Dict[str, int]:
    st.sidebar.markdown("### Stat Weights")
    return {
        stat: st.sidebar.slider(stat, 0, 100, default)
        for stat, default in DEFAULT_WEIGHTS.items()
    }


def _render_table(df: pd.DataFrame, label: str):
    if df.empty:
        st.info(f"*No {label.lower()} augments found.*")
        return
    cols_in_df = [c for c in STAT_ORDER if c in df.columns]
    st.subheader(label)
    st.dataframe(df[cols_in_df], use_container_width=True)


# ----------------------------------------------------------------------
# main render function (called by run_eq_aug_tool.py)
# ----------------------------------------------------------------------
def render():
    st.title(APP_TITLE)

    weights = _sidebar_weights()
    st.sidebar.markdown("### Upload inventory.txt")

    uploaded = st.sidebar.file_uploader(
        "Drag the Raidloot export here ↴", type=UPLOAD_TYPES["text"]
    )

    if not uploaded:
        st.info("Upload a Raidloot **/output inventory** export to begin.")
        return

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
