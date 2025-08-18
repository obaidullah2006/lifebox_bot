import sqlite3
from contextlib import contextmanager

DB_PATH = "lifebox.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn, open("models.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
        conn.commit()

@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def get_setting(key, default=None):
    with db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

def set_setting(key, value):
    with db() as conn:
        conn.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
