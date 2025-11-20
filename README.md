**Secure File Transfer Framework Chunk-Level Encryption & Dynamic Key Exchange for Local and Small Enterprise Networks**

A Secure File Transfer System designed for LAN/WLAN environments, featuring hybrid encryption, automatic file reception, and a relay server for offline delivery. Built using Python, Flask (TLS), and AES/RSA cryptography.

**🚀 Overview**

This system enables secure transmission of files across local networks by combining:

RSA (public key exchange)

AES-256 (chunk-level file encryption)

SHA-256 (integrity verification)

TLS/HTTPS (transport security)

It supports user registration, login, real-time file delivery, offline message queuing, and a GUI-based interface for sending and receiving files.

**⭐ Features**
**🔐 Hybrid Cryptography**

RSA-2048 for key exchange

AES-256 for encrypting each file chunk

SHA-256 hashing for integrity

Digital signing of public keys

**🧩 Chunk-Level Encryption**

Files split into smaller pieces

Each chunk encrypted independently

Supports resumable & faster transmission

Reduces data loss on failure

**📡 Network Architecture**

Works fully on local Wi-Fi/LAN

Clients + relay server communicate via HTTPS

Automatic receiver component runs on each client

**👤 User System**

Admission ID + Password login

User data stored in SQLite/JSON

Dynamic IP tracking for each user/device

**🖥 GUI**

Login screen

Registration

Dashboard with users list

File sending interface

Automatic decrypting receiver window

**📁 Project Structure**
<img width="789" height="525" alt="image" src="https://github.com/user-attachments/assets/190e7060-854c-4728-aa17-59b494b8fbff" />



⚙️ Requirements
Python Version: Python 3.10+
Install Dependencies
flask
flask_cors
pycryptodome
requests
werkzeug

**🚦 How to Run the System**
1️⃣ Start the Relay HTTPS Server
python app.py


Handles user registration

Key exchange

File routing

Offline delivery queue

Default:
https://<your-local-ip>:5000

2️⃣ Start the Client Application
python main.py


This launches the GUI:

Login

Dashboard

Send/Receive interface

3️⃣ Start the Auto-Receiver on Each Client
python encryption_sart/receive_server.py


This allows the user to receive encrypted files automatically.

🔄 How the System Works
1. Authentication

Users login using Admission ID + Password.

2. Key Exchange

Client requests recipient’s RSA public key from the relay.

3. Chunk Encryption

File → split → AES-256 encrypt each chunk → generate SHA-256 hash.

4. File Transmission

If recipient is online → send directly

If offline → relay queues file until they connect

5. Decryption

Receiver decrypts AES key, then decrypts chunks, then reassembles the file.

🔒 Security Model

End-to-end encryption via AES-256

RSA-2048 prevents key interception

All transmissions wrapped in HTTPS (TLS)

No plaintext stored on disk during transfer

Logs for auditing transfers

🛠 Future Improvements

Admin Web Dashboard

Multi-file sending

Peer-to-peer mode (no relay required)

Mobile app version

Packaging into Windows/Linux installers

👨‍💻 Author

Mark Gakobo (extreme-me)
Bachelor of Science in Computer Networks & Cyber Security
3rd Year Project – Secure File Transfer Framework
