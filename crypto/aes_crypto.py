from cryptography.fernet import Fernet
from crypto.key_manager import get_key
def encrypt_file(filename):
    master_key = get_key()
    master_cipher = Fernet(master_key)

    
    file_key = Fernet.generate_key()
    file_cipher = Fernet(file_key)

    
    with open(filename, "rb") as file:
        data = file.read()

    encrypted_data = file_cipher.encrypt(data)
    wrapped_key = master_cipher.encrypt(file_key)

    return encrypted_data, wrapped_key


def decrypt_file(encrypted_data, wrapped_key):
    
    master_key = get_key()
    master_cipher = Fernet(master_key)

    file_key = master_cipher.decrypt(wrapped_key)
    file_cipher = Fernet(file_key)
    decrypted_data = file_cipher.decrypt(encrypted_data)

    return decrypted_data
