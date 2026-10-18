from cryptography.fernet import Fernet
import os
from pathlib import Path


KEY_FILE = Path(
    os.getenv(
        "ENCRYPTION_KEY_FILE",
        Path(__file__).resolve().parents[1] / "secret.key",
    )
)

def generate_key():
    key = Fernet.generate_key()
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with KEY_FILE.open("wb") as key_file:
        key_file.write(key)
    return key    

def load_key():
    with KEY_FILE.open("rb") as file:
        key = file.read()
    return key

def get_key():
    if KEY_FILE.exists():
        return load_key()
    else:
        return generate_key()

