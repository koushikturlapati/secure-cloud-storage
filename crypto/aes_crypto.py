from cryptography.fernet import Fernet
from crypto.key_manager import get_key

key = get_key()
cipher = Fernet(key)


def encrypt_file(filename):
    with open(filename, "rb") as file:
        data = file.read()

    encrypted_data = cipher.encrypt(data)

    return encrypted_data


def decrypt_file(encrypted_data):
    decrypted_data = cipher.decrypt(encrypted_data)

    return decrypted_data


def encrypt_data(data):
    return cipher.encrypt(data)


def decrypt_data(encrypted_data):
    return cipher.decrypt(encrypted_data)