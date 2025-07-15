import tkinter as tk
from tkinter import ttk, messagebox
import requests

RELAY_SERVER = "https://192.168.0.26:5000"
ADMIN_AUTH = ("admin", "admin123")  # Replace for production use


def fetch_logs():
    try:
        r = requests.get(f"{RELAY_SERVER}/admin/logs", auth=ADMIN_AUTH, verify=False)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        messagebox.showerror("Error", f"Could not fetch logs: {e}")
        return []


def fetch_users():
    try:
        r = requests.get(f"{RELAY_SERVER}/admin/users", auth=ADMIN_AUTH, verify=False)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        messagebox.showerror("Error", f"Could not fetch users: {e}")
        return []


def fetch_sessions():
    try:
        r = requests.get(f"{RELAY_SERVER}/admin/active_sessions", auth=ADMIN_AUTH, verify=False)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        messagebox.showerror("Error", f"Could not fetch sessions: {e}")
        return []


def launch_admin_gui():
    root = tk.Tk()
    root.title("🛠 Admin Dashboard - Secure File Transfer")
    root.geometry("780x520")
    root.resizable(False, False)

    # Center window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (780 / 2))
    y = int((screen_height / 2) - (520 / 2))
    root.geometry(f"780x520+{x}+{y}")

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    # === LOGS TAB ===
    logs_tab = tk.Frame(notebook, padx=10, pady=10)
    logs_text = tk.Text(logs_tab, wrap="word", height=20)
    logs_text.pack(fill='both', expand=True, pady=(0, 10))

    def load_logs():
        logs_text.delete("1.0", tk.END)
        logs = fetch_logs()
        if logs:
            for log in logs:
                logs_text.insert(tk.END, f"[{log['timestamp']}] {log['from']} → {log['to']}: {log['filename']} ({log['chunk_count']} chunks)\n")
        else:
            logs_text.insert(tk.END, "No transfer logs found.")

    ttk.Button(logs_tab, text="🔄 Refresh Logs", command=load_logs).pack()

    # === USERS TAB ===
    users_tab = tk.Frame(notebook, padx=10, pady=10)
    user_listbox = tk.Listbox(users_tab, width=80, height=20)
    user_listbox.pack(pady=(0, 10))

    def load_users():
        user_listbox.delete(0, tk.END)
        users = fetch_users()
        if users:
            for user in users:
                if "error" in user:
                    user_listbox.insert(tk.END, f"[ERROR] {user['error']}")
                else:
                    user_listbox.insert(tk.END, f"{user['display_name']} ({user['admission_id']})")
        else:
            user_listbox.insert(tk.END, "No users found.")

    ttk.Button(users_tab, text="🔄 Refresh Users", command=load_users).pack()

    # === SESSIONS TAB ===
    sessions_tab = tk.Frame(notebook, padx=10, pady=10)
    session_listbox = tk.Listbox(sessions_tab, width=80, height=20)
    session_listbox.pack(pady=(0, 10))

    def load_sessions():
        session_listbox.delete(0, tk.END)
        sessions = fetch_sessions()
        if sessions:
            for session in sessions:
                session_listbox.insert(tk.END, f"{session['admission_id']} - Last Active: {session['last_active']}")
        else:
            session_listbox.insert(tk.END, "No active sessions found.")

    ttk.Button(sessions_tab, text="🔄 Refresh Sessions", command=load_sessions).pack()

    # Add tabs
    notebook.add(logs_tab, text="📜 Transfer Logs")
    notebook.add(users_tab, text="👥 Registered Users")
    notebook.add(sessions_tab, text="🟢 Active Sessions")

    # Initial load
    load_logs()
    load_users()
    load_sessions()

    root.mainloop()


if __name__ == "__main__":
    launch_admin_gui()
