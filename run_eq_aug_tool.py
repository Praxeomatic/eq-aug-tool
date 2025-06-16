# run_eq_aug_tool.py
import streamlit as st
from tool.ui.eq_aug_ui import render

# page config must be Streamlit's first command
st.set_page_config(
    page_title="EverQuest Augmentation Tool — DEV",
    page_icon="🧪",
    layout="wide",
)

if __name__ == "__main__":
    render()
