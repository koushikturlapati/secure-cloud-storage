# Secure Cloud Storage — Version 1 (Local-Only)

A secure, local-first encrypted file storage and collaboration application written in Python (FastAPI). Users can register accounts, establish secure cookie-backed sessions, upload files that are encrypted at rest with independent per-file keys, verify file integrity with SHA-256 upon download, organize files into folders, and share access with other registered users under granular read/write permissions.

---

## 1. Project Purpose & Architecture

Secure Cloud Storage Version 1 is designed to provide local, privacy-focused file storage without dependencies on third-party cloud services (no AWS, S3, KMS, or OAuth2). It combines **envelope encryption** with **secure server-side session management** to ensure confidentiality, integrity, and non-impersonation.

### Architectural Diagram

```
┌────────────────────────────────────────────────────────┐
│             Web Browser (frontend/)                    │
│   (index.html, dashboard.html, createacc.html, JS)     │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP (HttpOnly, SameSite Session Cookie)
                           ▼
┌────────────────────────────────────────────────────────┐
│               FastAPI Application (api/)               │
│                                                        │
│  ├── Routers:                                          │
│  │    ├── auth.py     (Register, Login, Logout, /me)   │
│  │    ├── files.py    (Upload, List, Download, Patch)  │
│  │    ├── folders.py  (Create, List, Delete)           │
│  │    └── shares.py   (Share, List Perms, Revoke)      │
│  │                                                     │
│  ├── Dependencies & Security (dependencies.py)         │
│  └── Schemas & Validation (schemas.py)                 │
└───────────────┬──────────────────────────┬─────────────┘
                │                          │
                ▼                          ▼
┌──────────────────────────────┐ ┌───────────────────────┐
│     Local MySQL Database     │ │   Local File System   │
│  - users                     │ │  - storage/           │
│  - auth_sessions (token hash)│ │    (unique UUIDs with │
│  - stored_files (wrapped key)│ │     ciphertext only)  │
│  - folders                   │ │  - secret.key         │
│  - file_permissions          │ │    (master key)       │
└──────────────────────────────┘ └───────────────────────┘
```

---

## 2. Core Features

- **Authentication & Sessions:**
  - Registration with username validation (3–50 chars, alphanumeric + `_-`) and bcrypt password hashing (min 8 chars).
  - Password verification during login.
  - Server-side opaque session tokens (`secrets.token_urlsafe(32)`).
  - Storage of SHA-256 hashes of session tokens in MySQL (`auth_sessions`).
  - Session tokens issued via `HttpOnly`, `SameSite=Lax`, and `Secure` (when HTTPS) cookies.
  - Expiration enforcement (24-hour default) and immediate database-backed session revocation on logout.
  - Strict prevention of user impersonation: `X-Username` and arbitrary `Authorization` headers are not trusted for identity.
- **Envelope File Encryption at Rest:**
  - Each uploaded file generates an independent per-file Fernet encryption key.
  - Plaintext data is encrypted using the file key before writing to disk.
  - The per-file key is wrapped (encrypted) with a local master Fernet key (`secret.key`).
  - Wrapped keys are stored securely alongside file metadata in MySQL.
  - Plaintext files are never written to disk; filenames are randomized UUIDs (`uuid.uuid4().hex`).
- **Cryptographic File Integrity:**
  - Plaintext SHA-256 hash calculated during upload and stored in MySQL.
  - SHA-256 verified in constant-time (`hmac.compare_digest`) upon download and decryption.
  - Downloads fail and are rejected if ciphertext or metadata has been corrupted or tampered with.
- **File Management:**
  - Upload, download, rename, and delete files.
  - Safe, atomic file writes using temporary files to prevent orphaned or partial files.
  - Sanitization against path traversal (rejects `../`, null bytes).
  - File size limits enforced (default 50 MB ceiling).
- **Hierarchical Folder Management:**
  - Nested folders with `parent_folder_id` relationships.
  - Cycle detection prevents circular parent hierarchies.
  - Prevention of non-empty folder deletion (rejects deleting folders containing subfolders or files).
- **Granular File Sharing & Permissions:**
  - File owners can share files with other registered users.
  - Permission levels:
    - **READ:** List shared files and download/decrypt them.
    - **WRITE:** All READ rights + authorized file content replacement (`PUT /files/{file_id}/content`).
    - **OWNER:** Rename, delete, share, and revoke access. Collaborators cannot delete or claim ownership.

---

## 3. Technology Stack

- **Python:** 3.11+
- **Backend Framework:** FastAPI, Starlette, Uvicorn
- **Database & ORM:** MySQL (local), SQLAlchemy 2.0+
- **Database Driver:** PyMySQL
- **Cryptography & Security:** `cryptography` (Fernet symmetric encryption), `bcrypt` (password hashing), Python `hashlib` (SHA-256)
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (Fetch API with cookie sessions)
- **Automated Testing:** `pytest`

---

## 4. Local MySQL Configuration

### Database Setup

1. Make sure MySQL Server (8.0+) is installed and running locally.
2. Connect to MySQL and create the database:

```sql
CREATE DATABASE IF NOT EXISTS secure_cloud CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
```

3. Run the schema script or migration:
   - Initial schema: `mysql -u root -p secure_cloud < database/secure_cloud.sql`
   - Version 1 migrations: `mysql -u root -p secure_cloud < database/migrations/01_v1_migration.sql`

---

## 5. Environment Variables

Configure these variables in a `.env` file in the project root:

```ini
# MySQL Database Connection Settings
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=secure_cloud

# Optional direct database connection string (overrides DB_* if specified)
# DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/secure_cloud

# Storage and Encryption Configuration
STORAGE_DIR=storage
ENCRYPTION_KEY_FILE=secret.key
MAX_UPLOAD_SIZE_BYTES=52428800
```

---

## 6. Installation & Execution

### 1. Create and Activate Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the Application

```powershell
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

The application is accessible at:
- **Web Interface:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive OpenAPI Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 7. API Reference

### Authentication (`api/routers/auth.py`)

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/createacc` | No | Register a new user account with bcrypt password |
| `POST` | `/login` | No | Verify credentials, issue session, set HttpOnly cookie |
| `POST` | `/logout` | Yes | Revoke server-side session token and clear cookie |
| `GET` | `/me` | Yes | Return authenticated user details |

### Files (`api/routers/files.py`)

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/files/upload` | Yes | Upload, encrypt, and store a file |
| `GET` | `/files/` | Yes | List files owned by or shared with the user |
| `GET` | `/files/{file_id}` | Yes | Download, decrypt, and verify SHA-256 integrity |
| `PATCH` | `/files/{file_id}` | Owner | Rename file (path traversal validated) |
| `DELETE` | `/files/{file_id}` | Owner | Delete file record and encrypted disk storage |
| `PUT` | `/files/{file_id}/content` | Owner/Write | Replace file content with new encrypted version |

### Folders (`api/routers/folders.py`)

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/folders/` | Yes | Create folder (supports parent_folder_id) |
| `GET` | `/folders/` | Yes | List folders owned by the authenticated user |
| `DELETE` | `/folders/{folder_id}` | Owner | Delete folder (blocks non-empty folders) |

### Sharing & Permissions (`api/routers/shares.py`)

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/files/{file_id}/share` | Owner | Grant or update read/write permission for a user |
| `GET` | `/files/{file_id}/permissions` | Owner | View access list and collaborators for a file |
| `DELETE` | `/files/{file_id}/share/{user_id}` | Owner | Revoke collaborator access |

---

## 8. Encryption & Authentication Workflows

### Envelope Encryption Lifecycle

1. **Upload:**
   - Raw bytes read into memory (under size limit).
   - Plaintext SHA-256 computed: `sha256_hash = hashlib.sha256(data).hexdigest()`.
   - Independent 256-bit Fernet key generated for the file: `file_key = Fernet.generate_key()`.
   - Data encrypted with `file_key`: `ciphertext = Fernet(file_key).encrypt(data)`.
   - `file_key` wrapped using local master key: `wrapped_key = Fernet(master_key).encrypt(file_key)`.
   - `ciphertext` written atomically to `storage/<uuid>.<ext>`.
   - `wrapped_key` and metadata saved in `stored_files` table.
2. **Download:**
   - Authorization verified (user is owner or has read/write permission).
   - `ciphertext` loaded from `storage/<uuid>.<ext>`.
   - `file_key` unwrapped using local master key.
   - Plaintext decrypted with `file_key`.
   - Computed SHA-256 verified against stored hash in constant time (`hmac.compare_digest`).
   - Plaintext streamed to client.

### Authentication Lifecycle

1. **Registration:** Username validated against length and character sets; password hashed using `bcrypt.gensalt()`.
2. **Login:** Credentials verified via `bcrypt.checkpw()`. A 256-bit cryptographically secure random token (`secrets.token_urlsafe(32)`) is generated.
3. **Storage:** Only the SHA-256 hash of the session token is stored in `auth_sessions`.
4. **Transport:** The raw token is sent to the browser in an `HttpOnly`, `SameSite=Lax` cookie.
5. **Authentication Verification:** On every request, `get_current_user` extracts the cookie, computes its SHA-256 hash, verifies the session in MySQL, and ensures it is active and not expired.
6. **Logout:** Session marked as `revoked=True` in database and cookie deleted from browser.

---

## 9. Automated Testing

The automated test suite runs against an isolated, temporary SQLite database and a sandboxed temporary storage directory, guaranteeing no side-effects on real local files or databases.

Run the entire test suite:

```powershell
python -m pytest -v
```

### Test Coverage Highlights

- **Authentication (`tests/test_auth.py`):** Registration, duplicate prevention, password validation, cookie issuance, bad passwords, 401 unauthenticated enforcement, header spoofing rejection, session expiration, and session revocation upon logout.
- **Files (`tests/test_files.py`):** Encrypted disk write verification, file listing, download decryption, SHA-256 verification, corrupted ciphertext rejection, tampered hash rejection, rename validation, atomic deletion, and path traversal prevention.
- **Folders (`tests/test_folders.py`):** Hierarchy creation, listing, invalid parent validation, rejection of deletion when containing subfolders or files, and clean deletion of empty folders.
- **Permissions (`tests/test_permissions.py`):** Access rejection for unauthorized users, read-only permissions, write-permission updates, collaborator restriction from owner operations (rename/delete), access revocation, and rejection of self-sharing.

---

## 10. Known Limitations (Version 1)

1. **Local-Only Single Node:** Version 1 is designed for a single machine running a local MySQL server and local filesystem storage.
2. **Local Master Key:** The master encryption key is stored on the local filesystem (`secret.key`). In a multi-tenant production environment, a hardware security module (HSM) or dedicated key vault would be used.
3. **Synchronous File I/O:** File uploads and downloads are read and decrypted locally in chunks/memory; very large files (> 500 MB) are capped to prevent local memory exhaustion.
