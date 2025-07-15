import tkinter as tk
from tkinter import messagebox, filedialog
import os
import requests
import base64
import json
import sys

from cryptography.hazmat.primitives import serialization



sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crypto_utils import (
    decrypt_aes_key_with_rsa,
    decrypt_chunk_with_aes,
    compute_sha256
)

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
WINDOW_WIDTH = 520
WINDOW_HEIGHT = 400
requests.packages.urllib3.disable_warnings()

def load_private_key(admission_id):
    private_key_path = f"private_key_{admission_id}.pem"
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"Private key file not found: {private_key_path}")

    with open(private_key_path, "rb") as key_file:
        return serialization.load_pem_private_key(key_file.read(), password=None)


def launch_receive_gui(admission_id, private_key_pem=None):
    root = tk.Tk()
    root.title(f"📥 Inbox - {admission_id}")
    root.resizable(False, False)

    # Center the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (WINDOW_WIDTH // 2)
    y = (screen_height // 2) - (WINDOW_HEIGHT // 2)
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    # === UI Layout ===
    tk.Label(root, text="📂 Received Files", font=("Arial", 14, "bold")).pack(pady=10)

    list_frame = tk.Frame(root)
    list_frame.pack(padx=10, pady=5, fill="both", expand=True)

    file_listbox = tk.Listbox(list_frame, width=60, height=10)
    file_listbox.pack()

    transfer_map = {}

    def refresh_file_list():
        file_listbox.delete(0, tk.END)
        transfer_map.clear()

        try:
            response = requests.get(f"{RELAY_SERVER}/transfers/{admission_id}", verify=False)
            if response.status_code == 200:
                transfers = response.json()
                if not transfers:
                    file_listbox.insert(tk.END, "No files available.")
                    return

                for transfer in transfers:
                    display = f'{transfer["filename"]} (from {transfer["from"]})'
                    file_listbox.insert(tk.END, display)
                    transfer_map[display] = transfer
            else:
                messagebox.showerror("Error", f"Failed to fetch transfers. Code: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def download_and_decrypt():
        selected = file_listbox.curselection()
        if not selected:
            messagebox.showwarning("No File", "Please select a file.")
            return

        selected_text = file_listbox.get(selected[0])
        transfer = transfer_map.get(selected_text)
        if not transfer:
            messagebox.showerror("Error", "Metadata not found for selected file.")
            return

        try:
            encrypted_key = transfer["encrypted_key"]
            chunks = transfer["chunks"]
            original_filename = transfer["filename"]

            if private_key_pem is None:
                private_key_obj = load_private_key(admission_id)
            else:
                private_key_obj = private_key_pem

            aes_key = decrypt_aes_key_with_rsa(encrypted_key, private_key_obj)

            decrypted_chunks = []
            for chunk in sorted(chunks, key=lambda x: x["index"]):
                chunk_bytes = base64.b64decode(chunk["data"])
                if compute_sha256(chunk_bytes) != chunk["hash"]:
                    raise ValueError(f"Hash mismatch in chunk {chunk['index']}")
                decrypted_chunks.append(decrypt_chunk_with_aes(chunk_bytes, aes_key))

            save_path = filedialog.asksaveasfilename(initialfile=original_filename)
            if not save_path:
                return

            with open(save_path, "wb") as f:
                for part in decrypted_chunks:
                    f.write(part)

            messagebox.showinfo("Success", f"✅ File saved to: {save_path}")

        except Exception as e:
            messagebox.showerror("Decryption Failed", f"{str(e)}")

    def go_back():
        root.destroy()
        from user.dashboard import launch_dashboard  # ✅ Fix circular import
        launch_dashboard(admission_id, display_name="You")

    # === Buttons ===
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="🔄 Refresh Inbox", width=20, command=refresh_file_list).pack(pady=5)
    tk.Button(button_frame, text="⬇️ Download & Decrypt", width=20, command=download_and_decrypt).pack(pady=5)
    tk.Button(button_frame, text="🔙 Back to Dashboard", width=20, command=go_back).pack(pady=5)

    refresh_file_list()
    root.mainloop()
