import os
import json
import sqlite3
from flask import request, jsonify
from functools import wraps

# === Base path relative to project root ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

LOG_FILE = os.path.join(BASE_DIR, "admin", "transfer_logs.json")
SESSION_FILE = os.path.join(BASE_DIR, "admin", "active_sessions.json")
DB_PATH = os.path.join(BASE_DIR, "database", "users.db")
TRANSFER_LOG_FILE = LOG_FILE

# === Hardcoded Admin Credentials (change in production) ===
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def require_admin_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

def load_transfer_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def load_active_sessions():
    if not os.path.exists(SESSION_FILE):
        return []
    with open(SESSION_FILE, "r") as f:
        return json.load(f)

def get_all_users():
    if not os.path.exists(DB_PATH):
        return []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT admission_id, display_name FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    except Exception as e:
        return [{"error": str(e)}]
