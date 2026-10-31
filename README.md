# Secure Cloud Storage

A small cloud file storage service written in Python. Users create an account,
upload files, and share them with other users. Every file is encrypted before
it is written to disk, and its SHA-256 hash is checked on download.
.

## Features

- Account creation and login with bcrypt-hashed passwords
- JWT access tokens (30 minutes) and refresh tokens (7 days, stored as hashes)
- Upload, list, download, and delete files
- Encryption at rest with Fernet (AES-128 in CBC mode with HMAC-SHA256)
- SHA-256 integrity check on every download
- Folders, and sharing files with other users
- A simple browser frontend served by the same app
- Docker image and a deployment guide for a single AWS EC2 instance

## Architecture

```
Browser (frontend/)
   │  HTTPS (planned)           Bearer JWT
   ▼
FastAPI app (api/main.py)
   ├── Auth: bcrypt, JWT, refresh tokens
   ├── Files, folders, sharing endpoints
   ├── crypto/      Fernet encryption, hashing, key management
   └── backend/     SQLAlchemy models and database session
        │                         │
        ▼                         ▼
   Encrypted blobs           SQLite (default)
   (STORAGE_DIR)             or MySQL (DB_* settings)
```

Key files:

| Path | Purpose |
|------|---------|
| `api/main.py` | FastAPI routes, auth, file and sharing logic |
| `api/dblogin_models.py` | Pydantic request and response models |
| `backend/models.py` | Database tables: users, stored files, folders, permissions, refresh tokens |
| `backend/database.py` | Database connection (SQLite or MySQL) |
| `crypto/aes_crypto.py` | Fernet encrypt and decrypt helpers |
| `crypto/key_manager.py` | Loads the encryption key, or creates one on first run |
| `crypto/hashing.py` | SHA-256 helper |
| `frontend/` | Login, dashboard, and account pages |
| `tests/test_auth.py` | Authentication tests |

## Requirements

- Python 3.11 or newer
- Or Docker and Docker Compose

## Quick start (local Python)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Signing secret for JWTs (required)
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

uvicorn api.main:app --reload
```

Open <http://127.0.0.1:8000>. The health check is at `/health`.

On first run the app creates:

- `database/app.db` (SQLite database)
- `storage/` (encrypted files)
- `secret.key` (Fernet encryption key)

## Quick start (Docker)

Create a `.env` file in the project root:

```text
SECRET_KEY=replace-with-a-long-random-secret
```

Then run:

```bash
docker compose up --build -d
```

Open <http://localhost:8000>. Data lives in the `app-data` Docker volume, so it
survives container rebuilds. See [DEPLOYMENT.md](DEPLOYMENT.md) for the AWS EC2
steps.

## Configuration

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `SECRET_KEY` | Yes | Read from `secret.key` if present | Signs JWT access tokens |
| `STORAGE_DIR` | No | `storage/` | Where encrypted files are written |
| `ENCRYPTION_KEY_FILE` | No | `secret.key` | Path to the Fernet key |
| `SQLITE_PATH` | No | `database/app.db` | SQLite file location |
| `DATABASE_URL` | No | — | Full SQLAlchemy URL, overrides everything else |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | No | — | MySQL settings (all five must be set) |

Keep `.env`, `secret.key`, and the `storage/` folder out of source control.
They are already listed in `.gitignore`.

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/createacc` | Create an account |
| POST | `/token` | Log in, returns access and refresh tokens |
| POST | `/refresh` | Get a new access token |
| POST | `/logout` | Revoke a refresh token |
| GET | `/me` | Current user |
| POST | `/files/upload` | Upload and encrypt a file |
| GET | `/files/` | List owned and shared files |
| GET | `/files/{id}` | Download a file (decrypted, hash checked) |
| DELETE | `/files/{id}` | Delete a file you own |
| POST | `/files/{id}/share` | Share a file with another user |
| GET | `/files/{id}/permissions` | See who has access |
| DELETE | `/files/{id}/share/{user_id}` | Remove a user's access |
| POST / GET / DELETE | `/folders` | Create, list, and delete folders |

Interactive API docs are available at `/docs` while the app is running.

## Running tests

```bash
pip install -r requirements.txt
pytest tests
```

The current tests cover authentication only. Encryption, file, and sharing
tests still need to be written.

## How encryption works

1. On upload, the file bytes are encrypted with a Fernet key and saved under a
   random UUID name in `STORAGE_DIR`.
2. The SHA-256 hash of the plaintext is stored in the database.
3. On download, the file is decrypted, its hash is recalculated, and the
   download is refused if the hash does not match.

Fernet authenticates the ciphertext, so tampering is detected during
decryption. The stored hash is an extra check on the plaintext.

## Limitations

- **Key storage:** the encryption key is stored on the same disk as the
  encrypted files. Anyone with access to the server can read the files. Moving
  the key into AWS KMS is planned.
- **Single instance:** SQLite and local file storage do not support multiple
  servers. Planned: S3 for file storage and a managed database.
- **Memory use:** files are read fully into memory for upload and download.
- **No HTTPS in the default setup:** add a reverse proxy with TLS before any
  public use.
- **Limited tests:** only authentication is covered.

## Roadmap

- [ ] Move the encryption key to AWS KMS
- [ ] Store encrypted files in S3
- [ ] Stream large uploads and downloads
- [ ] Store file sizes in the database instead of decrypting to measure them
- [ ] Tests for encryption, files, and sharing
- [ ] HTTPS with a domain name
- [ ] Remove the old prototype scripts in `crypto/` (`main.py`, `file_manager.py`, `verify_integrity.py`)

