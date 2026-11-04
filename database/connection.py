from contextlib import contextmanager
import mysql.connector
from config.settings import DATABASE_CONFIG

def get_connection():
    return mysql.connector.connect(**DATABASE_CONFIG)


@contextmanager
def connection_cursor(commit=False):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def register_user(telegram_id, username=None):
    query = """
        INSERT INTO users (telegram_id, username)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE username = VALUES(username)
    """
    with connection_cursor(commit=True) as cursor:
        cursor.execute(query, (telegram_id, username))
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
        return cursor.fetchone()["id"]
