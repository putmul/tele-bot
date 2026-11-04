"""Database queries used by the Telegram bot.

The repository keeps SQL out of Telegram handlers and makes it easier to
replace the storage layer later. Every query is scoped by the Telegram user
where applicable so users cannot access each other's records.
"""

from datetime import datetime

from database.connection import get_connection


def _user_id(telegram_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        row = cursor.fetchone()
        return row["id"] if row else None
    finally:
        cursor.close()
        connection.close()


def get_user_id(telegram_id):
    return _user_id(telegram_id)


def get_splits(telegram_id):
    user_id = _user_id(telegram_id)
    if not user_id:
        return []
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ws.id, ws.split_name, COUNT(se.id) AS exercise_count
            FROM workout_splits ws
            LEFT JOIN split_exercises se ON se.split_id = ws.id
            WHERE ws.user_id = %s AND ws.is_active = TRUE
            GROUP BY ws.id, ws.split_name
            ORDER BY ws.created_at, ws.id
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_split_exercises(telegram_id, split_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT e.id, e.exercise_name, se.exercise_order
            FROM split_exercises se
            JOIN exercises e ON e.id = se.exercise_id
            JOIN workout_splits ws ON ws.id = se.split_id
            WHERE se.split_id = %s AND ws.user_id = %s AND ws.is_active = TRUE
            ORDER BY se.exercise_order
            """,
            (split_id, user_id),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_split_by_number(telegram_id, number):
    splits = get_splits(telegram_id)
    index = number - 1
    return splits[index] if 0 <= index < len(splits) else None


def create_split(telegram_id, split_name, exercises, prs=None):
    """Create a split and its exercises.

    ``prs`` is a list matching ``exercises``. Each item is either None or a
    ``(weight_kg, repetitions)`` tuple.
    """
    user_id = _user_id(telegram_id)
    if not user_id:
        raise ValueError("User belum terdaftar. Jalankan /start terlebih dahulu.")
    prs = prs or [None] * len(exercises)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO workout_splits (user_id, split_name) VALUES (%s, %s)",
            (user_id, split_name),
        )
        split_id = cursor.lastrowid
        for order, (exercise_name, pr) in enumerate(zip(exercises, prs), start=1):
            cursor.execute(
                """
                INSERT INTO exercises (user_id, exercise_name) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
                """,
                (user_id, exercise_name),
            )
            exercise_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO split_exercises (split_id, exercise_id, exercise_order)
                VALUES (%s, %s, %s)
                """,
                (split_id, exercise_id, order),
            )
            if pr:
                weight, repetitions = pr
                estimated = weight * (1 + repetitions / 30)
                cursor.execute(
                    """
                    INSERT INTO personal_records
                        (user_id, exercise_id, weight_kg, repetitions, estimated_1rm)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, exercise_id, weight, repetitions, estimated),
                )
        connection.commit()
        return split_id
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def rename_split(telegram_id, split_id, new_name):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE workout_splits SET split_name = %s WHERE id = %s AND user_id = %s AND is_active = TRUE",
            (new_name, split_id, user_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()


def add_exercise_to_split(telegram_id, split_id, exercise_name):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id FROM workout_splits WHERE id = %s AND user_id = %s AND is_active = TRUE",
            (split_id, user_id),
        )
        if not cursor.fetchone():
            return False
        cursor.execute(
            """
            INSERT INTO exercises (user_id, exercise_name) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
            """,
            (user_id, exercise_name),
        )
        exercise_id = cursor.lastrowid
        cursor.execute(
            """
            SELECT COALESCE(MAX(exercise_order), 0) + 1 AS next_order
            FROM split_exercises WHERE split_id = %s
            """,
            (split_id,),
        )
        next_order = cursor.fetchone()["next_order"]
        cursor.execute(
            "INSERT INTO split_exercises (split_id, exercise_id, exercise_order) VALUES (%s, %s, %s)",
            (split_id, exercise_id, next_order),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def remove_exercise_from_split(telegram_id, split_id, exercise_number):
    exercises = get_split_exercises(telegram_id, split_id)
    index = exercise_number - 1
    if not 0 <= index < len(exercises):
        return False
    exercise = exercises[index]
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            DELETE se FROM split_exercises se
            JOIN workout_splits ws ON ws.id = se.split_id
            WHERE se.split_id = %s AND se.exercise_id = %s AND ws.user_id = %s
            """,
            (split_id, exercise["id"], user_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()


def reorder_exercise(telegram_id, split_id, from_number, to_number):
    """Move an exercise to another position inside a split."""
    exercises = get_split_exercises(telegram_id, split_id)
    from_index = from_number - 1
    to_index = to_number - 1
    if not (0 <= from_index < len(exercises) and 0 <= to_index < len(exercises)):
        return False
    moved = exercises.pop(from_index)
    exercises.insert(to_index, moved)
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        # The temporary offset avoids collisions with the unique order key.
        cursor.execute(
            """
            UPDATE split_exercises se
            JOIN workout_splits ws ON ws.id = se.split_id
            SET se.exercise_order = se.exercise_order + 1000
            WHERE se.split_id = %s AND ws.user_id = %s AND ws.is_active = TRUE
            """,
            (split_id, user_id),
        )
        for order, exercise in enumerate(exercises, start=1):
            cursor.execute(
                "UPDATE split_exercises SET exercise_order = %s WHERE id = %s",
                (order, exercise["id"]),
            )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def delete_split(telegram_id, split_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE workout_splits SET is_active = FALSE WHERE id = %s AND user_id = %s AND is_active = TRUE",
            (split_id, user_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()


def get_active_session(telegram_id):
    user_id = _user_id(telegram_id)
    if not user_id:
        return None
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT s.id, s.split_id, s.started_at, s.current_exercise_order,
                   ws.split_name
            FROM workout_sessions s
            JOIN workout_splits ws ON ws.id = s.split_id
            WHERE s.user_id = %s AND s.status = 'active'
            LIMIT 1
            """,
            (user_id,),
        )
        session = cursor.fetchone()
        if not session:
            return None
        cursor.execute(
            """
            SELECT e.id, e.exercise_name, se.exercise_order
            FROM split_exercises se
            JOIN exercises e ON e.id = se.exercise_id
            WHERE se.split_id = %s
            ORDER BY se.exercise_order
            """,
            (session["split_id"],),
        )
        session["exercises"] = cursor.fetchall()
        return session
    finally:
        cursor.close()
        connection.close()


def create_session(telegram_id, split_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT id FROM workout_sessions WHERE user_id = %s AND status = 'active' LIMIT 1",
            (user_id,),
        )
        if cursor.fetchone():
            return None
        cursor.execute(
            """
            INSERT INTO workout_sessions (user_id, split_id, current_exercise_order)
            SELECT %s, id, 1 FROM workout_splits
            WHERE id = %s AND user_id = %s AND is_active = TRUE
            """,
            (user_id, split_id, user_id),
        )
        connection.commit()
        return cursor.lastrowid if cursor.rowcount else None
    finally:
        cursor.close()
        connection.close()


def update_session_position(telegram_id, session_id, position):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE workout_sessions SET current_exercise_order = %s
            WHERE id = %s AND user_id = %s AND status = 'active'
            """,
            (position, session_id, user_id),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def add_workout_set(telegram_id, session_id, exercise_id, weight, repetitions):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id FROM workout_sessions WHERE id = %s AND user_id = %s AND status = 'active'",
            (session_id, user_id),
        )
        if not cursor.fetchone():
            return
        cursor.execute(
            "SELECT COALESCE(MAX(set_number), 0) + 1 AS next_set FROM workout_sets WHERE session_id = %s AND exercise_id = %s",
            (session_id, exercise_id),
        )
        set_number = cursor.fetchone()["next_set"]
        cursor.execute(
            "INSERT INTO workout_sets (session_id, exercise_id, set_number, repetitions, weight_kg) VALUES (%s, %s, %s, %s, %s)",
            (session_id, exercise_id, set_number, repetitions, weight),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def get_current_pr(telegram_id, exercise_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT weight_kg, repetitions, estimated_1rm, achieved_at
            FROM personal_records
            WHERE user_id = %s AND exercise_id = %s
            ORDER BY estimated_1rm DESC, achieved_at DESC
            LIMIT 1
            """,
            (user_id, exercise_id),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def get_last_session_set(telegram_id, exercise_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ws.weight_kg, ws.repetitions, ws.set_number, s.ended_at
            FROM workout_sets ws
            JOIN workout_sessions s ON s.id = ws.session_id
            WHERE s.user_id = %s AND ws.exercise_id = %s AND s.status = 'completed'
            ORDER BY s.ended_at DESC, ws.set_number DESC
            LIMIT 1
            """,
            (user_id, exercise_id),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def record_pr(telegram_id, exercise_id, weight, repetitions):
    user_id = _user_id(telegram_id)
    estimated = weight * (1 + repetitions / 30)
    current = get_current_pr(telegram_id, exercise_id)
    is_new = not current or estimated > float(current["estimated_1rm"])
    connection = get_connection()
    cursor = connection.cursor()
    try:
        if is_new:
            cursor.execute(
                """
                INSERT INTO personal_records
                    (user_id, exercise_id, weight_kg, repetitions, estimated_1rm)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, exercise_id, weight, repetitions, estimated),
            )
            connection.commit()
    finally:
        cursor.close()
        connection.close()
    return is_new, estimated


def complete_session(telegram_id, session_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT started_at, split_id FROM workout_sessions WHERE id = %s AND user_id = %s AND status = 'active'",
            (session_id, user_id),
        )
        session = cursor.fetchone()
        if not session:
            return None
        ended_at = datetime.now()
        started_at = session["started_at"]
        duration = max(0, int((ended_at - started_at).total_seconds()))
        cursor.execute(
            """
            UPDATE workout_sessions
            SET status = 'completed', ended_at = %s, duration_seconds = %s
            WHERE id = %s AND user_id = %s
            """,
            (ended_at, duration, session_id, user_id),
        )
        connection.commit()
        return {"duration_seconds": duration, "split_id": session["split_id"]}
    finally:
        cursor.close()
        connection.close()


def complete_session_with_pending_sets(telegram_id, session_id, pending_sets, pending_prs):
    """Commit a workout buffer and complete its session atomically.

    ``pending_sets`` and ``pending_prs`` are dictionaries keyed by exercise ID.
    Exercises without a recorded set are stored as ``0 kg x 0 reps`` so the
    completed session has one entry for every exercise in its split.
    """
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT started_at, split_id
            FROM workout_sessions
            WHERE id = %s AND user_id = %s AND status = 'active'
            """,
            (session_id, user_id),
        )
        session = cursor.fetchone()
        if not session:
            return None

        cursor.execute(
            """
            SELECT e.id
            FROM split_exercises se
            JOIN exercises e ON e.id = se.exercise_id
            WHERE se.split_id = %s
            ORDER BY se.exercise_order
            """,
            (session["split_id"],),
        )
        exercise_rows = cursor.fetchall()
        for exercise in exercise_rows:
            exercise_id = exercise["id"]
            value = pending_sets.get(exercise_id) or pending_sets.get(str(exercise_id))
            weight = value["weight"] if value else 0
            repetitions = value["repetitions"] if value else 0
            cursor.execute(
                """
                INSERT INTO workout_sets
                    (session_id, exercise_id, set_number, repetitions, weight_kg)
                VALUES (%s, %s, 1, %s, %s)
                """,
                (session_id, exercise_id, repetitions, weight),
            )

        for exercise_id, value in pending_prs.items():
            exercise_id = int(exercise_id)
            cursor.execute(
                """
                SELECT COALESCE(MAX(estimated_1rm), 0) AS current_1rm
                FROM personal_records
                WHERE user_id = %s AND exercise_id = %s
                """,
                (user_id, exercise_id),
            )
            current_1rm = float(cursor.fetchone()["current_1rm"] or 0)
            if value["estimated_1rm"] > current_1rm:
                cursor.execute(
                    """
                    INSERT INTO personal_records
                        (user_id, exercise_id, weight_kg, repetitions, estimated_1rm)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        exercise_id,
                        value["weight"],
                        value["repetitions"],
                        value["estimated_1rm"],
                    ),
                )

        ended_at = datetime.now()
        duration = max(0, int((ended_at - session["started_at"]).total_seconds()))
        cursor.execute(
            """
            UPDATE workout_sessions
            SET status = 'completed', ended_at = %s, duration_seconds = %s
            WHERE id = %s AND user_id = %s AND status = 'active'
            """,
            (ended_at, duration, session_id, user_id),
        )
        connection.commit()
        return {"duration_seconds": duration, "split_id": session["split_id"]}
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def save_cardio(telegram_id, activity_type, speed, duration):
    user_id = _user_id(telegram_id)
    distance = speed * duration / 60
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO cardio_logs (user_id, activity_type, speed_kmh, duration_minutes, distance_km) VALUES (%s, %s, %s, %s, %s)",
            (user_id, activity_type, speed, duration, distance),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()
    return distance


def save_body_measurement(telegram_id, weight, height_cm):
    user_id = _user_id(telegram_id)
    height_m = height_cm / 100
    bmi = weight / (height_m * height_m)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO body_logs (user_id, weight_kg, height_cm, bmi) VALUES (%s, %s, %s, %s)",
            (user_id, weight, height_cm, bmi),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()
    return bmi


def get_statistics(telegram_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS total_workouts,
                   COALESCE(SUM(duration_seconds), 0) AS total_duration,
                   COALESCE(SUM((SELECT COUNT(*) FROM workout_sets x WHERE x.session_id = s.id)), 0) AS total_sets
            FROM workout_sessions s
            WHERE s.user_id = %s AND s.status = 'completed'
            """,
            (user_id,),
        )
        summary = cursor.fetchone()
        cursor.execute(
            """
            SELECT e.exercise_name, pr.weight_kg, pr.repetitions, pr.estimated_1rm
            FROM personal_records pr
            JOIN exercises e ON e.id = pr.exercise_id
            WHERE pr.user_id = %s
              AND pr.estimated_1rm = (
                  SELECT MAX(pr2.estimated_1rm) FROM personal_records pr2
                  WHERE pr2.user_id = pr.user_id AND pr2.exercise_id = pr.exercise_id
              )
            ORDER BY e.exercise_name
            """,
            (user_id,),
        )
        summary["prs"] = cursor.fetchall()
        return summary
    finally:
        cursor.close()
        connection.close()


def add_reminders(telegram_id, days, reminder_time):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        for day in days:
            cursor.execute(
                """
                INSERT INTO gym_reminders (user_id, day_of_week, reminder_time)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE is_active = TRUE
                """,
                (user_id, day, reminder_time),
            )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def get_active_reminders(telegram_id=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT gr.*, u.telegram_id
            FROM gym_reminders gr
            JOIN users u ON u.id = gr.user_id
            WHERE gr.is_active = TRUE
        """
        params = ()
        if telegram_id is not None:
            query += " AND gr.user_id = (SELECT id FROM users WHERE telegram_id = %s)"
            params = (telegram_id,)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_user_reminders(telegram_id, active_only=True):
    """Return a user's reminders, including their database IDs."""
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        query = "SELECT id, day_of_week, reminder_time, is_active FROM gym_reminders WHERE user_id = %s"
        if active_only:
            query += " AND is_active = TRUE"
        query += " ORDER BY day_of_week, reminder_time, id"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def deactivate_reminder(telegram_id, reminder_id):
    user_id = _user_id(telegram_id)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE gym_reminders SET is_active = FALSE WHERE id = %s AND user_id = %s",
            (reminder_id, user_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()
