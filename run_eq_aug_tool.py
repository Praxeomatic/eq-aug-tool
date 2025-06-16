"""
Entry-point for Streamlit.

• If tool.ui.eq_aug_ui exposes a `render()` function (newer layout), call it.
• Otherwise just import the module so its top-level code runs
  (older “Beautiful” pink/purple/black layout).
"""

import importlib
import streamlit as st

# first Streamlit call
st.set_page_config(
    page_title="EverQuest Augmentation Tool — DEV",
    page_icon="🧪",
    layout="wide",
)

ui_module = importlib.import_module("tool.ui.eq_aug_ui")

if hasattr(ui_module, "render"):
    ui_module.render()  # newer versions
# else: merely importing ui_module has already executed the original layout
