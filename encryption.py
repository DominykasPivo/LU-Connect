from cryptography.fernet import Fernet
import base64
import os

# Path to store the encryption key
KEY_FILE = 'encryption_key.key'

def generate_key():
    """Generate a new encryption key and save it to a file"""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
    
    # Return the key
    with open(KEY_FILE, 'rb') as key_file:
        return key_file.read()

def get_encryption_key():
    """Get the encryption key or generate a new one if it doesn't exist"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as key_file:
            return key_file.read()
    else:
        return generate_key()

def encrypt_message(message):
    """Encrypt a message using the encryption key"""
    if isinstance(message, str):
        message = message.encode()
    
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_message = f.encrypt(message)
    return encrypted_message

def decrypt_message(encrypted_message):
    """Decrypt a message using the encryption key"""
    key = get_encryption_key()
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)
    return decrypted_message.decode()
