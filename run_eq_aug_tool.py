"""
EverQuest Augmentation Tool – Streamlit launcher
Run with:
    streamlit run run_eq_aug_tool.py
"""
import streamlit as st

# Page-wide configuration – must be first Streamlit command
st.set_page_config(page_title="EQ Aug Tool v2", layout="wide")

# Import UI module (registers `render`)
from tool.ui.eq_aug_ui import render   # noqa: E402

# Draw the UI on every rerun
render()
