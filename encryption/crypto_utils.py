import os
import hashlib
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


# === AES KEY GENERATION ===
def generate_aes_key():
    return get_random_bytes(32)  # 256-bit AES key


# === CHUNK FILE ===
def split_file_into_chunks(file_path, chunk_size=1024 * 1024):  # 1MB default
    chunks = []
    with open(file_path, 'rb') as f:
        index = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            chunks.append((index, data))
            index += 1
    return chunks


# === SHA-256 HASHING ===
def compute_sha256(data):
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()


# === AES ENCRYPTION ===
def encrypt_chunk_with_aes(chunk_data, aes_key):
    cipher = AES.new(aes_key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(chunk_data, AES.block_size))
    return cipher.iv + ciphertext  # Prepend IV for decryption


def decrypt_chunk_with_aes(encrypted_data, aes_key):
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)


# === RSA ENCRYPTION OF AES KEY ===
def encrypt_aes_key_with_rsa(aes_key, recipient_rsa_public_key_pem):
    public_key = RSA.import_key(recipient_rsa_public_key_pem)
    cipher_rsa = PKCS1_OAEP.new(public_key)
    encrypted_key = cipher_rsa.encrypt(aes_key)
    return base64.b64encode(encrypted_key).decode()


def decrypt_aes_key_with_rsa(encrypted_key_b64, private_key_pem):
    encrypted_key = base64.b64decode(encrypted_key_b64)
    private_key = RSA.import_key(private_key_pem)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    return cipher_rsa.decrypt(encrypted_key)
