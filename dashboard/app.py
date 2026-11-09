"""Entrypoint Streamlit dengan navigasi sidebar kustom."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st


st.set_page_config(
    page_title="GymBuddy",
    layout="wide",
)

halaman = st.navigation(
    [
        st.Page(
            "pages/dashboard.py",
            title="Dashboard",
            default=True,
        ),
        st.Page(
            "pages/aktivitas_workout_cardio.py",
            title="Latihan & Kardio",
        ),
    ]
)

halaman.run()
