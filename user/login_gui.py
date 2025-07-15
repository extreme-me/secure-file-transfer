import json
import tkinter as tk
from tkinter import messagebox
import requests
import bcrypt
import os
import sys
import subprocess
from dashboard import launch_dashboard


# === Server Address ===
config_path = os.path.join(os.path.dirname(__file__), "..", "relay", "config.json")

if not os.path.exists(config_path):
    raise FileNotFoundError("Missing config.json file in relay/ directory.")

with open(config_path, "r") as f:
    config = json.load(f)

relay_host = config.get("relay_host", "127.0.0.1")
relay_port = config.get("relay_port", 5000)

# Construct the full server URL
RELAY_SERVER = f"https://{relay_host}:{relay_port}"
# === Centered Fixed Size ===
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 350

def center_window(win, width, height):
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    win.geometry(f"{width}x{height}+{x}+{y}")

def login_user():
    admission_id = admission_id_entry.get().strip().upper()
    password = password_entry.get()

    if not admission_id or not password:
        messagebox.showerror("Input Error", "All fields are required.")
        return

    try:
        response = requests.get(f"{RELAY_SERVER}/users/{admission_id}", verify=False)

        if response.status_code == 404:
            messagebox.showerror("Login Failed", "User not found.")
            return

        if response.status_code != 200:
            messagebox.showerror("Login Failed", f"Server error: {response.status_code}")
            return

        user_data = response.json()
        stored_hash = user_data.get('password_hash')

        if not stored_hash:
            messagebox.showerror("Login Failed", "User data incomplete.")
            return

        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
            messagebox.showinfo("Login Success", f"Welcome {user_data['display_name']}")

            # ✅ Report session activity to admin
            try:
                requests.post(
                    f"{RELAY_SERVER}/admin/active_sessions",
                    json={"admission_id": admission_id},
                    verify=False
                )
            except Exception as e:
                print(f"⚠️ Session logging failed: {e}")

            root.destroy()
            launch_dashboard(admission_id, user_data['display_name'])
        else:
            messagebox.showerror("Login Failed", "Incorrect password.")

    except requests.exceptions.SSLError:
        messagebox.showerror("Connection Error", "SSL Certificate Error. Is your server using HTTPS correctly?")
    except requests.exceptions.ConnectionError as ce:
        messagebox.showerror("Connection Error", f"Connection failed:\n{ce}")
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error:\n{e}")

def go_to_register():
    root.destroy()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    register_path = os.path.join(base_dir, "register_gui.py")
    subprocess.Popen([sys.executable, register_path])

# === GUI Setup ===
root = tk.Tk()
root.title("Login - Secure File Transfer")
center_window(root, WINDOW_WIDTH, WINDOW_HEIGHT)
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True)

tk.Label(frame, text="Login", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=(0, 20))

tk.Label(frame, text="Admission ID:").grid(row=1, column=0, sticky="e", pady=5)
admission_id_entry = tk.Entry(frame, width=30)
admission_id_entry.grid(row=1, column=1, pady=5)

tk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e", pady=5)
password_entry = tk.Entry(frame, show="*", width=30)
password_entry.grid(row=2, column=1, pady=5)

tk.Button(frame, text="Login", command=login_user, width=20).grid(row=3, column=0, columnspan=2, pady=15)

# 👇 Register redirect
tk.Label(frame, text="Don't have an account?").grid(row=4, column=0, pady=(10, 0))
tk.Button(frame, text="Register Here", command=go_to_register, width=20).grid(row=4, column=1, pady=(10, 0))

root.mainloop()
