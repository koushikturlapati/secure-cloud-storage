import os
import json
from crypto.aes_crypto import encrypt_file, decrypt_file
from crypto.metadata import save_metadata
from datetime import datetime
from crypto.hashing import get_file_hash
METADATA_FILE = "metadata.json"

def upload_file(filename):
    os.makedirs("storage", exist_ok=True)
    file_hash = get_file_hash(filename)
    """ENCRYPTING THE GIVE FILE"""
    encrypted_data = encrypt_file(filename)

    encrypted_filename = os.path.basename(filename) + ".enc"

    destination = os.path.join("storage", encrypted_filename)

    """SAVING THE ENCRYTPED FILE"""
    with open(destination, "wb") as file:
            file.write(encrypted_data)
    file_hash = get_file_hash(filename)
    metadata = {
        "original_filename": filename,
        "encrypted_filename": encrypted_filename,
        "file_hash": file_hash,
        "uploaded_time": str(datetime.now())
    }        
    save_metadata(metadata)
    print(f"File uploaded: {destination}")


def download_file(encrypted_file):
    encrypted_filename = os.path.join("storage", encrypted_file)

    with open(encrypted_filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = decrypt_file(encrypted_data)
    output_filename = encrypted_file.removesuffix(".enc") 
    # ------ INTEGRITY CHECK-----

    #getting the stored data from metadata
    with open(METADATA_FILE, "r") as file:
        metadata = json.load(file)
    stored_hash = None
    for item in metadata:
        if item["encrypted_filename"] == encrypted_file:
            stored_hash = item["file_hash"]
            break
    
    if stored_hash and stored_hash == get_file_hash(output_filename):
        print("Integrity check passed.")
    else:
        print("Integrity check failed.")

if __name__ == "__main__":
    upload_file("hello.txt" )    
    download_file("hello.txt.enc")