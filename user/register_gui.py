import json
import tkinter as tk
from tkinter import messagebox
import requests
import os
import bcrypt
import subprocess
import sys
import urllib3

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# === CONFIGURATION ===
# Load server config from relay/config.json
config_path = os.path.join(os.path.dirname(__file__), "..", "relay", "config.json")

if not os.path.exists(config_path):
    raise FileNotFoundError("Missing config.json file in relay/ directory.")

with open(config_path, "r") as f:
    config = json.load(f)

relay_host = config.get("relay_host", "127.0.0.1")
relay_port = config.get("relay_port", 5000)

# Construct the full server URL
RELAY_SERVER = f"https://{relay_host}:{relay_port}"
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 300

# ✅ Suppress SSL warnings (only in development with self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === RSA Key Pair Generation ===
def generate_rsa_key_pair(admission_id):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open(f"private_key_{admission_id}.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return public_pem.decode()

# === Registration Logic ===
def register_user():
    admission_id = admission_id_entry.get().strip().upper()
    display_name = display_name_entry.get().strip()
    password = password_entry.get()
    confirm_password = confirm_password_entry.get()

    if not all([admission_id, display_name, password, confirm_password]):
        messagebox.showerror("Input Error", "All fields are required.")
        return

    if password != confirm_password:
        messagebox.showerror("Password Error", "Passwords do not match.")
        return

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    public_key_pem = generate_rsa_key_pair(admission_id)

    payload = {
        "admission_id": admission_id,
        "password_hash": password_hash,
        "display_name": display_name,
        "public_key": public_key_pem
    }

    try:
        response = requests.post(f"{RELAY_SERVER}/register", json=payload, verify=False)
        if response.status_code == 201:
            messagebox.showinfo("Success", f"User registered successfully!\nAdmission ID: {admission_id}")
            root.destroy()
            subprocess.Popen([sys.executable, "login_gui.py"])  # 🔁 Redirect to login
        elif response.status_code == 409:
            messagebox.showwarning("Error", "Admission ID already exists.")
        else:
            messagebox.showerror("Server Error", response.text)
    except Exception as e:
        messagebox.showerror("Connection Error", str(e))

# === GUI SETUP ===
root = tk.Tk()
root.title("Register - Secure File Transfer")
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.resizable(False, False)

# Center the window on screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_pos = (screen_width // 2) - (WINDOW_WIDTH // 2)
y_pos = (screen_height // 2) - (WINDOW_HEIGHT // 2)
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x_pos}+{y_pos}")

# === Widgets ===
tk.Label(root, text="Admission ID:").pack(pady=5)
admission_id_entry = tk.Entry(root, width=30)
admission_id_entry.pack()

tk.Label(root, text="Display Name:").pack(pady=5)
display_name_entry = tk.Entry(root, width=30)
display_name_entry.pack()

tk.Label(root, text="Password:").pack(pady=5)
password_entry = tk.Entry(root, show="*", width=30)
password_entry.pack()

tk.Label(root, text="Confirm Password:").pack(pady=5)
confirm_password_entry = tk.Entry(root, show="*", width=30)
confirm_password_entry.pack()

tk.Button(root, text="Register", command=register_user, width=20).pack(pady=15)

root.mainloop()
