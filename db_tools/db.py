import sqlite3
import json


def get_db_connection(db_path, timeout=300):
    return sqlite3.connect(db_path, timeout=timeout)


def create_table_if_not_exists(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS output_files (
            id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            inputs TEXT NOT NULL,
            extra_fields TEXT
        )
        """
    )
    conn.commit()


def ensure_extra_fields_column(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(output_files)")
    columns = [row[1] for row in cursor.fetchall()]
    if "extra_fields" not in columns:
        cursor.execute("ALTER TABLE output_files ADD COLUMN extra_fields TEXT")
        conn.commit()


def add_entry_to_database(conn, filename, inputs, extra_fields):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO output_files (filename, inputs, extra_fields) VALUES (?, ?, ?)",
        (
            filename,
            json.dumps(inputs),
            json.dumps(extra_fields) if extra_fields else None,
        ),
    )
    conn.commit()


def fetch_inputs(conn, filename):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT inputs, extra_fields FROM output_files WHERE filename = ?", (filename,)
    )
    result = cursor.fetchone()
    if result:
        inputs = json.loads(result[0])
        extra_fields = json.loads(result[1]) if result[1] else {}
        return inputs, extra_fields
    return None, None


def count_entries(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM output_files")
    result = cursor.fetchone()
    return result[0] if result else 0


def delete_db_entry(conn, filename):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM output_files WHERE filename = ?", (filename,))
    conn.commit()
