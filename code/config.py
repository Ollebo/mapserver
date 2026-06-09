import os
import sqlite3

import requests


DB_PATH = os.environ.get("TERRACOTTA_DB_PATH", "/data/db/terracotta.sqlite")


def _connect():
    return sqlite3.connect(DB_PATH, timeout=5)


def ensure_settings_table():
    try:
        conn = _connect()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS settings ("
            "key TEXT PRIMARY KEY, "
            "value TEXT NOT NULL, "
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("settings: ensure_settings_table failed: {0}".format(e))


def get_setting(key, default=None):
    try:
        conn = _connect()
        cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else default
    except Exception as e:
        print("settings: get_setting({0}) failed: {1}".format(key, e))
        return default


def set_setting(key, value):
    try:
        conn = _connect()
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) "
            "VALUES (?, ?, CURRENT_TIMESTAMP)",
            (key, value),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("settings: set_setting({0}) failed: {1}".format(key, e))


def ollebo_key():
    return get_setting("ollebo_key") or os.environ.get("OLLEBO_KEY", "")


def terracotta_public_url():
    return (
        get_setting("terracotta_public_url")
        or os.environ.get("TERRACOTTA_PUBLIC_URL", "http://localhost:5001")
    )


def api_url():
    return os.environ.get("API", "https://www.ollebo.com/api/v1")


def check_connection(timeout=5):
    key = ollebo_key()
    if not key:
        return False, "No map key configured"
    try:
        resp = requests.get(
            api_url(),
            headers={"Authorization": "Bearer " + key},
            timeout=timeout,
        )
        if 200 <= resp.status_code < 400:
            return True, "HTTP {0}".format(resp.status_code)
        return False, "HTTP {0}".format(resp.status_code)
    except requests.RequestException as e:
        return False, str(e)
