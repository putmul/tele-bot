"""Halaman utama dashboard GymBuddy."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import DASHBOARD_TELEGRAM_ID
from dashboard.services.analytics import (
    get_body_progress,
    get_combined_activity_history,
    get_dashboard_summary,
    get_recent_activities,
)


st.set_page_config(
    page_title="GymBuddy Dashboard",
    layout="wide",
)


def _get_telegram_id():
    """Mengubah ID dashboard dari environment menjadi integer yang valid."""
    if not DASHBOARD_TELEGRAM_ID:
        return None
    try:
        return int(DASHBOARD_TELEGRAM_ID)
    except ValueError:
        return None


def _format_duration(minutes):
    minutes = float(minutes or 0)
    hours, remaining_minutes = divmod(int(round(minutes)), 60)
    if hours:
        return f"{hours} jam {remaining_minutes} menit"
    return f"{remaining_minutes} menit"


def _format_metric(value, suffix=""):
    if value is None or pd.isna(value):
        return "-"
    formatted = f"{float(value):,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted}{suffix}"


def _show_body_progress(telegram_id):
    st.subheader("Progres tubuh")
    body_df = get_body_progress(telegram_id)

    if body_df.empty:
        st.info("Belum ada data berat badan atau tinggi badan.")
        return

    metric_options = {
        "Berat badan": ("weight_kg", "kg"),
        "Tinggi badan": ("height_cm", "cm"),
        "BMI": ("bmi", ""),
    }
    selected_metric = st.selectbox(
        "Pilih metrik",
        list(metric_options),
        key="body_progress_metric",
    )
    column, unit = metric_options[selected_metric]
    selected_data = body_df.dropna(subset=[column]).copy()

    if selected_data.empty:
        st.info(f"Belum ada data untuk metrik {selected_metric.lower()}.")
        return

    latest_value = selected_data[column].iloc[-1]
    latest_date = pd.to_datetime(selected_data["recorded_at"].iloc[-1]).strftime("%d-%m-%Y")
    st.metric(
        f"{selected_metric} terbaru",
        _format_metric(latest_value, f" {unit}" if unit else ""),
        help=f"Pengukuran terakhir pada {latest_date}",
    )

    figure = px.line(
        selected_data,
        x="recorded_at",
        y=column,
        markers=True,
        labels={
            "recorded_at": "Tanggal",
            column: f"{selected_metric} ({unit})" if unit else selected_metric,
        },
        title=f"Progres {selected_metric}",
    )
    figure.update_layout(hovermode="x unified", margin=dict(t=60, b=20))
    st.plotly_chart(figure, use_container_width=True)


def _show_activity_overview(telegram_id):
    st.subheader("Ringkasan aktivitas")
    activity_df = get_combined_activity_history(telegram_id)

    if activity_df.empty:
        st.info("Belum ada data latihan atau kardio.")
        return

    activity_df["activity_at"] = pd.to_datetime(activity_df["activity_at"])
    activity_df["jenis_aktivitas"] = activity_df["activity_type"].map(
        {"Workout": "Latihan", "Cardio": "Kardio"}
    )
    activity_df["minggu"] = activity_df["activity_at"].dt.to_period("W").dt.start_time
    weekly = (
        activity_df.groupby(["minggu", "jenis_aktivitas"], as_index=False)
        .size()
        .rename(columns={"size": "jumlah_aktivitas"})
    )
    figure = px.bar(
        weekly,
        x="minggu",
        y="jumlah_aktivitas",
        color="jenis_aktivitas",
        barmode="group",
        labels={
            "minggu": "Minggu",
            "jumlah_aktivitas": "Jumlah aktivitas",
            "jenis_aktivitas": "Jenis aktivitas",
        },
        title="Aktivitas latihan dan kardio per minggu",
    )
    figure.update_layout(hovermode="x unified", margin=dict(t=60, b=20))
    st.plotly_chart(figure, use_container_width=True)


def _show_recent_activities(telegram_id):
    st.subheader("Aktivitas terbaru")
    recent_df = get_recent_activities(telegram_id)
    if recent_df.empty:
        st.info("Belum ada aktivitas terbaru.")
        return

    display_df = recent_df.copy()
    display_df["Tanggal"] = pd.to_datetime(display_df["activity_at"]).dt.strftime("%d-%m-%Y %H:%M")
    display_df["Tipe"] = display_df["activity_type"].map(
        {"Workout": "Latihan", "Cardio": "Kardio"}
    )
    display_df["Aktivitas"] = display_df["activity_name"]
    display_df["Durasi"] = display_df["duration_minutes"].apply(_format_duration)
    display_df["Jarak (km)"] = display_df["distance_km"].apply(
        lambda value: _format_metric(value, " km") if pd.notna(value) else "-"
    )
    st.dataframe(
        display_df[["Tanggal", "Tipe", "Aktivitas", "Durasi", "Jarak (km)"]],
        use_container_width=True,
        hide_index=True,
    )


telegram_id = _get_telegram_id()
if telegram_id is None:
    st.error(
        "Konfigurasi DASHBOARD_TELEGRAM_ID belum diisi atau tidak valid. "
        "Tambahkan Telegram ID user pada file .env."
    )
    st.stop()

st.title("GymBuddy Dashboard")

try:
    summary = get_dashboard_summary(telegram_id)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total latihan", summary["total_workouts"])
    col2.metric("Total kardio", summary["total_cardio"])
    col3.metric("Total durasi", _format_duration(summary["total_duration_minutes"]))
    col4.metric("Jarak kardio", _format_metric(summary["total_distance_km"], " km"))

    st.divider()
    _show_body_progress(telegram_id)

    st.divider()
    _show_activity_overview(telegram_id)

    st.divider()
    _show_recent_activities(telegram_id)
except Exception as error:
    st.error(f"Dashboard tidak dapat mengambil data: {error}")
