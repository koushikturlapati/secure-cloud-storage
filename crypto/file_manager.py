import os
import shutil
from aes_crypto import encrypt_file, decrypt_file

def upload_file(filename):
    os.makedirs("storage", exist_ok=True)

    encrypted_data = encrypt_file(filename)
    encrypted_filename = os.path.basename(filename) + ".enc"
    destination = os.path.join("storage", encrypted_filename)
    with open(destination, "wb") as file:
        file.write(encrypted_data)
    print(f"File uploaded: {destination}")


upload_file("hello.txt" )
def download_file(encrypted_file):
    encrypted_filename = os.path.join("storage", encrypted_file)
    with open(encrypted_filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = decrypt_file(encrypted_data)
    output_filename = encrypted_file.removesuffix(".enc") 
    with open(output_filename, "wb") as file:
        file.write(decrypted_data)
    print(f"File downloaded: {output_filename}")
download_file("hello.txt.enc")