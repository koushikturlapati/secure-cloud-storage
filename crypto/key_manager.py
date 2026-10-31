
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

    with KEY_FILE.open("xb") as key_file:
        key_file.write(key)

    return key


def load_key():
    with KEY_FILE.open("rb") as file:
        key = file.read()

    # Validate that the stored key is a valid Fernet key.
    Fernet(key)

    return key


def get_key():
    if KEY_FILE.exists():
        return load_key()

    try:
        return generate_key()
    except FileExistsError:
        # Another process may have created the key simultaneously.
        return load_key()
