import os
import sys
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify

# === Append project root to sys.path ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# === Local imports (after fixing sys.path) ===
from db import initialize_db, get_db_connection
from admin.admin_utils import (
    require_admin_auth,
    load_transfer_logs,
    load_active_sessions,
    get_all_users, SESSION_FILE
)

# === Initialize Flask app ===
app = Flask(__name__)
initialize_db()

# === Paths ===
from admin.admin_utils import TRANSFER_LOG_FILE as TRANSFER_LOG_PATH

@app.route('/')
def index():
    return "✅ Secure File Transfer Relay Server is Running"

# === Register New User ===
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    admission_id = data.get('admission_id')
    password_hash = data.get('password_hash')
    display_name = data.get('display_name')
    public_key = data.get('public_key')

    if not all([admission_id, password_hash, display_name, public_key]):
        return jsonify({"error": "Missing fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (admission_id, password_hash, display_name, public_key)
            VALUES (?, ?, ?, ?)
        ''', (admission_id, password_hash, display_name, public_key))
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Admission ID already exists"}), 409
    finally:
        conn.close()


# === User Registration ===
@app.route("/admin/active_sessions", methods=["POST"])
def update_active_sessions():
    data = request.get_json()
    admission_id = data.get("admission_id")
    timestamp = datetime.now().isoformat()

    session_entry = {"admission_id": admission_id, "last_active": timestamp}

    try:
        # ✅ Ensure the folder exists
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)

        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                sessions = json.load(f)
        else:
            sessions = []

        sessions = [s for s in sessions if s["admission_id"] != admission_id]
        sessions.append(session_entry)

        with open(SESSION_FILE, "w") as f:
            json.dump(sessions, f, indent=2)

        return jsonify({"message": "Session updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === List All Users ===
@app.route('/users', methods=['GET'])
def list_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT admission_id, display_name FROM users')
    users = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in users])

# === Get User by ID ===
@app.route('/users/<admission_id>', methods=['GET'])
def get_user(admission_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE admission_id = ?', (admission_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user))

# === Receive a File Transfer ===
@app.route('/transfer', methods=['POST'])
def receive_transfer():
    data = request.get_json()
    required_fields = ['from', 'to', 'encrypted_key', 'filename', 'chunks']

    if not all(data.get(k) for k in required_fields):
        return jsonify({"error": "Missing transfer data"}), 400

    recipient_dir = os.path.join(os.path.dirname(__file__), "..", "transfers", data['to'])
    os.makedirs(recipient_dir, exist_ok=True)

    transfer_path = os.path.join(recipient_dir, f"{data['filename']}.meta.json")

    with open(transfer_path, "w") as f:
        json.dump(data, f)

    # === Log transfer ===
    log_transfer({
        "timestamp": datetime.now().isoformat(),
        "from": data['from'],
        "to": data['to'],
        "filename": data['filename'],
        "chunk_count": len(data['chunks'])
    })

    return jsonify({"message": "Transfer stored"}), 200

# === Inbox Fetch ===
@app.route('/transfers/<admission_id>', methods=['GET'])
def get_transfers_for_user(admission_id):
    user_dir = os.path.join(os.path.dirname(__file__), "..", "transfers", admission_id)
    if not os.path.exists(user_dir):
        return jsonify([])

    transfers = []
    for fname in os.listdir(user_dir):
        if fname.endswith(".meta.json"):
            with open(os.path.join(user_dir, fname), "r") as f:
                metadata = json.load(f)
                transfers.append(metadata)

    return jsonify(transfers)

# === Helper: Log transfers for admin ===
def log_transfer(entry):
    os.makedirs(os.path.dirname(TRANSFER_LOG_PATH), exist_ok=True)
    if os.path.exists(TRANSFER_LOG_PATH):
        with open(TRANSFER_LOG_PATH, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(entry)

    with open(TRANSFER_LOG_PATH, "w") as f:
        json.dump(logs, f, indent=2)

# === ADMIN ROUTES ===
@app.route("/admin/logs", methods=["GET"])
@require_admin_auth
def get_logs():
    return jsonify(load_transfer_logs())

@app.route("/admin/users", methods=["GET"])
@require_admin_auth
def get_all_users_route():
    return jsonify(get_all_users())

@app.route("/admin/active_sessions", methods=["GET"])
@require_admin_auth
def get_active_sessions_route():
    return jsonify(load_active_sessions())

# === Launch HTTPS server ===
if __name__ == "__main__":
    # Load config.json for IP and port
    config_path = os.path.join(os.path.dirname(__file__), "config.json")  # adjust path if needed
    if not os.path.exists(config_path):
        raise FileNotFoundError("Missing config.json file for relay_host and relay_port!")

    with open(config_path, "r") as f:
        cfg = json.load(f)

    app.run(
        host=cfg.get("relay_host", "127.0.0.1"),
        port=cfg.get("relay_port", 5000),
        ssl_context=('cert.pem', 'key.pem')
    )
