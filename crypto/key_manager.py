from cryptography.fernet import Fernet
import os

def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)
    return key    

def load_key():
    with open("secret.key", "rb") as file:
        key = file.read()
    return key

def get_key():
    if os.path.exists("secret.key"):
        return load_key()
    else:
        return generate_key()

key = get_key()
