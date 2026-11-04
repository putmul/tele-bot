"""Streamlit dashboard entry point."""

import streamlit as st

from config.settings import API_BASE_URL

st.set_page_config(page_title="GymBuddy Dashboard", page_icon="🏋️", layout="wide")
st.title("GymBuddy Dashboard")
st.caption("Dashboard awal untuk memantau aktivitas gym dari Telegram Bot.")

st.info(
    f"Backend API: {API_BASE_URL}. Halaman visualisasi akan ditambahkan bertahap "
    "setelah endpoint database tersedia."
)
