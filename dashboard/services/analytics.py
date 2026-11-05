"""Query read-only untuk visualisasi dashboard GymBuddy."""

import pandas as pd
import streamlit as st

from database.connection import connection_cursor


def _fetch_one(query, params=()):
    with connection_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def _fetch_all(query, params=()):
    with connection_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def _dataframe(rows, columns=None):
    frame = pd.DataFrame(rows)
    if columns and frame.empty:
        return pd.DataFrame(columns=columns)
    return frame


def _date_conditions(column, start_date=None, end_date=None):
    conditions = []
    params = []
    if start_date:
        conditions.append(f"DATE({column}) >= %s")
        params.append(start_date)
    if end_date:
        conditions.append(f"DATE({column}) <= %s")
        params.append(end_date)
    return conditions, params


@st.cache_data(ttl=60, show_spinner=False)
def get_dashboard_summary(telegram_id):
    """Mengambil KPI dashboard dan body measurement terbaru."""
    user = _fetch_one("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    if not user:
        return {
            "total_workouts": 0,
            "total_cardio": 0,
            "total_duration_minutes": 0,
            "total_distance_km": 0,
            "latest_body": None,
        }

    user_id = user["id"]
    workout = _fetch_one(
        """
        SELECT COUNT(*) AS total_workouts,
               COALESCE(SUM(duration_seconds), 0) AS duration_seconds
        FROM workout_sessions
        WHERE user_id = %s AND status = 'completed'
        """,
        (user_id,),
    )
    cardio = _fetch_one(
        """
        SELECT COUNT(*) AS total_cardio,
               COALESCE(SUM(duration_minutes), 0) AS duration_minutes,
               COALESCE(SUM(distance_km), 0) AS distance_km
        FROM cardio_logs
        WHERE user_id = %s
        """,
        (user_id,),
    )
    latest_body = _fetch_one(
        """
        SELECT weight_kg, height_cm, bmi, recorded_at
        FROM body_logs
        WHERE user_id = %s
        ORDER BY recorded_at DESC, id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    return {
        "total_workouts": int(workout["total_workouts"] or 0),
        "total_cardio": int(cardio["total_cardio"] or 0),
        "total_duration_minutes": float(workout["duration_seconds"] or 0) / 60
        + float(cardio["duration_minutes"] or 0),
        "total_distance_km": float(cardio["distance_km"] or 0),
        "latest_body": latest_body,
    }


@st.cache_data(ttl=60, show_spinner=False)
def get_body_progress(telegram_id):
    rows = _fetch_all(
        """
        SELECT recorded_at, weight_kg, height_cm, bmi
        FROM body_logs
        WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)
        ORDER BY recorded_at, id
        """,
        (telegram_id,),
    )
    frame = _dataframe(rows, ["recorded_at", "weight_kg", "height_cm", "bmi"])
    if not frame.empty:
        frame["recorded_at"] = pd.to_datetime(frame["recorded_at"])
    return frame


def _activity_query(telegram_id, start_date=None, end_date=None, limit=None):
    workout_conditions, workout_dates = _date_conditions("s.started_at", start_date, end_date)
    cardio_conditions, cardio_dates = _date_conditions("c.recorded_at", start_date, end_date)
    workout_where = " AND ".join(
        [
            "s.user_id = (SELECT id FROM users WHERE telegram_id = %s)",
            "s.status = 'completed'",
            *workout_conditions,
        ]
    )
    cardio_where = " AND ".join(
        ["c.user_id = (SELECT id FROM users WHERE telegram_id = %s)", *cardio_conditions]
    )

    workout_rows = _fetch_all(
        f"""
        SELECT s.started_at AS activity_at,
               'Workout' AS activity_type,
               ws.split_name AS activity_name,
               COALESCE(s.duration_seconds, 0) / 60 AS duration_minutes,
               NULL AS distance_km
        FROM workout_sessions s
        JOIN workout_splits ws ON ws.id = s.split_id
        WHERE {workout_where}
        """,
        (telegram_id, *workout_dates),
    )
    cardio_rows = _fetch_all(
        f"""
        SELECT c.recorded_at AS activity_at,
               'Cardio' AS activity_type,
               c.activity_type AS activity_name,
               c.duration_minutes,
               c.distance_km
        FROM cardio_logs c
        WHERE {cardio_where}
        """,
        (telegram_id, *cardio_dates),
    )
    frame = _dataframe(
        [*workout_rows, *cardio_rows],
        ["activity_at", "activity_type", "activity_name", "duration_minutes", "distance_km"],
    )
    if frame.empty:
        return frame
    frame["activity_at"] = pd.to_datetime(frame["activity_at"])
    frame = frame.sort_values("activity_at", ascending=False).reset_index(drop=True)
    return frame.head(limit) if limit else frame


@st.cache_data(ttl=60, show_spinner=False)
def get_combined_activity_history(telegram_id, start_date=None, end_date=None):
    return _activity_query(telegram_id, start_date, end_date)


@st.cache_data(ttl=60, show_spinner=False)
def get_recent_activities(telegram_id):
    return _activity_query(telegram_id, limit=10)


@st.cache_data(ttl=60, show_spinner=False)
def get_exercise_options(telegram_id):
    rows = _fetch_all(
        """
        SELECT DISTINCT e.exercise_name
        FROM exercises e
        JOIN workout_sets ws ON ws.exercise_id = e.id
        JOIN workout_sessions s ON s.id = ws.session_id
        WHERE s.user_id = (SELECT id FROM users WHERE telegram_id = %s)
          AND s.status = 'completed'
        ORDER BY e.exercise_name
        """,
        (telegram_id,),
    )
    return [row["exercise_name"] for row in rows]


@st.cache_data(ttl=60, show_spinner=False)
def get_workout_progress(telegram_id, exercise_name, start_date=None, end_date=None):
    date_conditions, dates = _date_conditions("s.started_at", start_date, end_date)
    conditions = [
        "s.user_id = (SELECT id FROM users WHERE telegram_id = %s)",
        "s.status = 'completed'",
        "e.exercise_name = %s",
        *date_conditions,
    ]
    rows = _fetch_all(
        f"""
        SELECT DATE(s.started_at) AS activity_date,
               e.exercise_name,
               MAX(ws.weight_kg) AS max_weight_kg,
               MAX(ws.weight_kg * (1 + ws.repetitions / 30)) AS estimated_1rm,
               MAX(ws.repetitions) AS max_repetitions
        FROM workout_sets ws
        JOIN workout_sessions s ON s.id = ws.session_id
        JOIN exercises e ON e.id = ws.exercise_id
        WHERE {' AND '.join(conditions)}
        GROUP BY DATE(s.started_at), e.id, e.exercise_name
        ORDER BY activity_date
        """,
        (telegram_id, exercise_name, *dates),
    )
    frame = _dataframe(
        rows,
        ["activity_date", "exercise_name", "max_weight_kg", "estimated_1rm", "max_repetitions"],
    )
    if not frame.empty:
        frame["activity_date"] = pd.to_datetime(frame["activity_date"])
    return frame


@st.cache_data(ttl=60, show_spinner=False)
def get_cardio_types(telegram_id):
    rows = _fetch_all(
        """
        SELECT DISTINCT activity_type
        FROM cardio_logs
        WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)
        ORDER BY activity_type
        """,
        (telegram_id,),
    )
    return [row["activity_type"] for row in rows]


@st.cache_data(ttl=60, show_spinner=False)
def get_cardio_progress(telegram_id, activity_type=None, start_date=None, end_date=None):
    date_conditions, dates = _date_conditions("c.recorded_at", start_date, end_date)
    conditions = [
        "c.user_id = (SELECT id FROM users WHERE telegram_id = %s)",
        *date_conditions,
    ]
    params = [telegram_id, *dates]
    if activity_type:
        conditions.append("c.activity_type = %s")
        params.append(activity_type)
    rows = _fetch_all(
        f"""
        SELECT c.recorded_at AS activity_date,
               c.activity_type,
               c.speed_kmh,
               c.duration_minutes,
               c.distance_km
        FROM cardio_logs c
        WHERE {' AND '.join(conditions)}
        ORDER BY activity_date
        """,
        tuple(params),
    )
    frame = _dataframe(
        rows,
        ["activity_date", "activity_type", "speed_kmh", "duration_minutes", "distance_km"],
    )
    if not frame.empty:
        frame["activity_date"] = pd.to_datetime(frame["activity_date"])
    return frame
