"""Halaman gabungan riwayat dan progres latihan serta kardio."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import DASHBOARD_TELEGRAM_ID
from dashboard.services.analytics import (
    get_cardio_progress,
    get_cardio_types,
    get_combined_activity_history,
    get_exercise_options,
    get_workout_progress,
)


def _get_telegram_id():
    try:
        return int(DASHBOARD_TELEGRAM_ID)
    except (TypeError, ValueError):
        return None


def _period_filter():
    default_end = date.today()
    default_start = default_end - timedelta(days=90)
    selected = st.date_input(
        "Periode data",
        value=(default_start, default_end),
        format="DD/MM/YYYY",
    )
    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        return selected[0], selected[1]
    return default_start, default_end


def _format_duration(minutes):
    minutes = float(minutes or 0)
    hours, remaining = divmod(int(round(minutes)), 60)
    return f"{hours} jam {remaining} menit" if hours else f"{remaining} menit"


def _history_tab(telegram_id, start_date, end_date):
    activity_df = get_combined_activity_history(telegram_id, start_date, end_date)
    if activity_df.empty:
        st.info("Tidak ada aktivitas pada periode yang dipilih.")
        return

    type_filter = st.selectbox(
        "Filter jenis aktivitas",
        ["Semua", "Latihan", "Kardio"],
        key="activity_type_filter",
    )
    filtered = activity_df
    internal_type = {"Latihan": "Workout", "Kardio": "Cardio"}.get(type_filter)
    if internal_type:
        filtered = filtered[filtered["activity_type"] == internal_type]

    if filtered.empty:
        st.info("Tidak ada aktivitas untuk filter tersebut.")
        return

    chart_data = (
        filtered.assign(
            tanggal=filtered["activity_at"].dt.date,
            jenis_aktivitas=filtered["activity_type"].map(
                {"Workout": "Latihan", "Cardio": "Kardio"}
            ),
        )
        .groupby(["tanggal", "jenis_aktivitas"], as_index=False)
        .size()
        .rename(columns={"size": "jumlah_aktivitas"})
    )
    figure = px.bar(
        chart_data,
        x="tanggal",
        y="jumlah_aktivitas",
        color="jenis_aktivitas",
        barmode="group",
        labels={
            "tanggal": "Tanggal",
            "jumlah_aktivitas": "Jumlah aktivitas",
            "jenis_aktivitas": "Jenis aktivitas",
        },
        title="Aktivitas berdasarkan tanggal",
    )
    st.plotly_chart(figure, use_container_width=True)

    display = filtered.copy()
    display["Tanggal"] = display["activity_at"].dt.strftime("%d-%m-%Y %H:%M")
    display["Tipe"] = display["activity_type"].map(
        {"Workout": "Latihan", "Cardio": "Kardio"}
    )
    display["Aktivitas"] = display["activity_name"]
    display["Durasi"] = display["duration_minutes"].apply(_format_duration)
    display["Jarak (km)"] = display["distance_km"].apply(
        lambda value: f"{float(value):.2f}" if pd.notna(value) else "-"
    )
    st.dataframe(
        display[["Tanggal", "Tipe", "Aktivitas", "Durasi", "Jarak (km)"]],
        use_container_width=True,
        hide_index=True,
    )


def _workout_progress_tab(telegram_id, start_date, end_date):
    exercises = get_exercise_options(telegram_id)
    if not exercises:
        st.info("Belum ada data progres latihan.")
        return

    exercise = st.selectbox("Pilih latihan", exercises, key="progress_exercise")
    metric_options = {
        "Berat maksimum": ("max_weight_kg", "kg"),
        "1RM estimasi": ("estimated_1rm", "kg"),
        "Repetisi maksimum": ("max_repetitions", "repetisi"),
    }
    metric = st.selectbox("Pilih metrik progres", list(metric_options), key="workout_metric")
    column, unit = metric_options[metric]
    progress_df = get_workout_progress(telegram_id, exercise, start_date, end_date)
    if progress_df.empty:
        st.info("Belum ada progres untuk latihan dan periode tersebut.")
        return

    figure = px.line(
        progress_df,
        x="activity_date",
        y=column,
        markers=True,
        labels={"activity_date": "Tanggal", column: f"{metric} ({unit})"},
        title=f"Progres {exercise} - {metric}",
    )
    figure.update_layout(hovermode="x unified")
    st.plotly_chart(figure, use_container_width=True)


def _cardio_progress_tab(telegram_id, start_date, end_date):
    cardio_types = get_cardio_types(telegram_id)
    if not cardio_types:
        st.info("Belum ada data progres kardio.")
        return

    activity_type = st.selectbox("Pilih jenis kardio", cardio_types, key="progress_cardio_type")
    metric_options = {
        "Jarak": ("distance_km", "km"),
        "Durasi": ("duration_minutes", "menit"),
        "Kecepatan": ("speed_kmh", "km/jam"),
    }
    metric = st.selectbox("Pilih metrik progres", list(metric_options), key="cardio_metric")
    column, unit = metric_options[metric]
    progress_df = get_cardio_progress(telegram_id, activity_type, start_date, end_date)
    if progress_df.empty:
        st.info("Belum ada progres kardio pada periode tersebut.")
        return

    figure = px.line(
        progress_df,
        x="activity_date",
        y=column,
        markers=True,
        labels={"activity_date": "Tanggal", column: f"{metric} ({unit})"},
        title=f"Progres {activity_type} - {metric}",
    )
    figure.update_layout(hovermode="x unified")
    st.plotly_chart(figure, use_container_width=True)


telegram_id = _get_telegram_id()
if telegram_id is None:
    st.error(
        "Konfigurasi DASHBOARD_TELEGRAM_ID belum diisi atau tidak valid. "
        "Tambahkan Telegram ID user pada file .env."
    )
    st.stop()

st.title("Latihan & Kardio")
st.caption("Riwayat dan progres aktivitas latihan serta kardio dalam satu halaman.")
start_date, end_date = _period_filter()

if start_date > end_date:
    st.error("Tanggal awal tidak boleh lebih besar dari tanggal akhir.")
    st.stop()

try:
    history_tab, progress_tab = st.tabs(["Riwayat", "Progres"])
    with history_tab:
        _history_tab(telegram_id, start_date, end_date)
    with progress_tab:
        workout_tab, cardio_tab = st.tabs(["Latihan", "Kardio"])
        with workout_tab:
            _workout_progress_tab(telegram_id, start_date, end_date)
        with cardio_tab:
            _cardio_progress_tab(telegram_id, start_date, end_date)
except Exception as error:
    st.error(f"Data aktivitas tidak dapat dimuat: {error}")
