import json
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import requests
import base64
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_utils import (
    generate_aes_key,
    encrypt_aes_key_with_rsa,
    split_file_into_chunks,
    encrypt_chunk_with_aes,
    compute_sha256
)

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
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 300

def launch_send_gui(sender_id, recipient_id):
    root = tk.Tk()
    root.title("📤 Send File - Secure Transfer")
    root.resizable(False, False)

    # Center window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (WINDOW_WIDTH / 2))
    y = int((screen_height / 2) - (WINDOW_HEIGHT / 2))
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    selected_file = tk.StringVar()

    def select_file():
        file_path = filedialog.askopenfilename()
        if file_path:
            selected_file.set(file_path)

    def send_file():
        file_path = selected_file.get()
        if not file_path:
            messagebox.showwarning("No File Selected", "Please select a file to send.")
            return

        try:
            aes_key = generate_aes_key()

            # Fetch recipient's public key
            response = requests.get(f"{RELAY_SERVER}/users/{recipient_id}", verify=False)
            if response.status_code != 200:
                messagebox.showerror("Error", "Failed to fetch recipient public key.")
                return

            recipient_data = response.json()
            public_key_pem = recipient_data['public_key']

            encrypted_aes_key = encrypt_aes_key_with_rsa(aes_key, public_key_pem)
            chunks = split_file_into_chunks(file_path)

            encrypted_chunks = []
            for index, chunk in chunks:
                encrypted = encrypt_chunk_with_aes(chunk, aes_key)
                encrypted_chunks.append({
                    "index": index,
                    "data": base64.b64encode(encrypted).decode(),
                    "hash": compute_sha256(encrypted)
                })

            payload = {
                "from": sender_id,
                "to": recipient_id,
                "encrypted_key": encrypted_aes_key,
                "filename": os.path.basename(file_path),
                "chunks": encrypted_chunks
            }

            result = requests.post(f"{RELAY_SERVER}/transfer", json=payload, verify=False)
            if result.status_code == 200:
                messagebox.showinfo("Success", "✅ File sent successfully!")
                root.destroy()
            else:
                messagebox.showerror("Server Error", f"Failed to send file.\n{result.text}")

        except Exception as e:
            messagebox.showerror("Send Error", str(e))

    # === UI Layout ===
    tk.Label(root, text=f"Recipient: {recipient_id}", font=("Arial", 12, "bold")).pack(pady=(20, 10))

    entry_frame = tk.Frame(root)
    entry_frame.pack(pady=5)
    tk.Entry(entry_frame, textvariable=selected_file, width=40, state='readonly').grid(row=0, column=0, padx=5)
    tk.Button(entry_frame, text="📁 Browse", command=select_file).grid(row=0, column=1, padx=5)

    tk.Button(root, text="🚀 Send File", width=25, command=send_file).pack(pady=25)

    root.mainloop()
