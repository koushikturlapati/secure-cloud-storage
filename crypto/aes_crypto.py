
from cryptography.fernet import Fernet
from crypto.key_manager import get_key


def encrypt_data(file_data: bytes) -> tuple[bytes, bytes]:
    
    master_key = get_key()
    master_cipher = Fernet(master_key)

    file_key = Fernet.generate_key()
    file_cipher = Fernet(file_key)

    encrypted_data = file_cipher.encrypt(file_data)
    wrapped_key = master_cipher.encrypt(file_key)

    return encrypted_data, wrapped_key


def decrypt_data(
    encrypted_data: bytes,
    wrapped_key: bytes
) -> bytes:
    
    master_key = get_key()
    master_cipher = Fernet(master_key)

    file_key = master_cipher.decrypt(wrapped_key)
    file_cipher = Fernet(file_key)

    return file_cipher.decrypt(encrypted_data)
