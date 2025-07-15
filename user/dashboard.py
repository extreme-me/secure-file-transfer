import json
import tkinter as tk
from tkinter import messagebox
import requests
import urllib3
import os

from encryption.send_gui import launch_send_gui
from encryption.receiver_gui import launch_receive_gui

# === CONFIG ===
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
WINDOW_WIDTH = 450
WINDOW_HEIGHT = 400

# Suppress HTTPS warnings (for self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def launch_dashboard(admission_id, display_name):
    def refresh_user_list():
        try:
            response = requests.get(f"{RELAY_SERVER}/users", verify=False)
            if response.status_code == 200:
                user_listbox.delete(0, tk.END)
                users = response.json()
                if not users:
                    user_listbox.insert(tk.END, "No other users found.")
                    return
                for user in users:
                    if user["admission_id"] != admission_id:
                        user_listbox.insert(tk.END, f'{user["display_name"]} ({user["admission_id"]})')
            else:
                messagebox.showerror("Error", f"Failed to fetch users. Code: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect:\n{e}")

    def send_file():
        selected = user_listbox.curselection()
        if not selected:
            messagebox.showwarning("No recipient", "Please select a recipient.")
            return

        selected_text = user_listbox.get(selected[0])

        try:
            if "(" not in selected_text or ")" not in selected_text:
                raise ValueError("Recipient ID format is invalid.")

            recipient_admission_id = selected_text.split("(")[-1].replace(")", "").strip()
            launch_send_gui(admission_id, recipient_admission_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse recipient ID.\nDetails: {str(e)}")

    def open_inbox():
        try:
            private_key_path = os.path.join(os.path.dirname(__file__), f"private_key_{admission_id}.pem")
            if not os.path.exists(private_key_path):
                messagebox.showerror("Missing Key", f"Private key not found for {admission_id}")
                return

            with open(private_key_path, "rb") as f:
                private_key_pem = f.read()

            root.destroy()
            launch_receive_gui(admission_id, private_key_pem)
        except Exception as e:
            messagebox.showerror("Inbox Error", f"Failed to open inbox:\n{e}")


    def logout():
        print("Logout clicked")
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            root.destroy()


    # === GUI Setup ===
    root = tk.Tk()
    root.title("📂 Dashboard - Secure File Transfer")
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.resizable(False, False)

    # Center the window on screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (WINDOW_WIDTH // 2)
    y = (screen_height // 2) - (WINDOW_HEIGHT // 2)
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    # === Layout ===
    tk.Label(root, text=f"Welcome, {display_name}", font=("Arial", 14, "bold")).pack(pady=15)

    user_frame = tk.LabelFrame(root, text="Available Users", padx=10, pady=10)
    user_frame.pack(padx=15, pady=10, fill="x")

    user_listbox = tk.Listbox(user_frame, width=40, height=8)
    user_listbox.pack(pady=5)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=15, fill="x", expand=True)

    tk.Button(button_frame, text="🔄 Refresh", width=20, command=refresh_user_list).pack(pady=5)
    tk.Button(button_frame, text="📤 Send File", width=20, command=send_file).pack(pady=5)
    tk.Button(button_frame, text="📥 Open Inbox", width=20, command=open_inbox).pack(pady=5)
    tk.Button(button_frame, text="🚪 Logout", width=20, command=logout).pack(pady=5)

    refresh_user_list()
    root.mainloop()
