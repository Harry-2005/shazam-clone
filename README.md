# shazam-clone

This repository is a scaffold and working prototype for a Shazam-like application (backend + web + mobile). Below is a concise, step-by-step log of what has been created and changed so far, plus commands to reproduce and next recommended steps.

**Current Structure**
- **backend**: Python backend service (FastAPI-ready)
  - [backend/app](backend/app): application code
  - [backend/tests](backend/tests): test scripts
  - [backend/.env](backend/.env): environment variables
  - [backend/requirements.txt](backend/requirements.txt): installed packages
  - [backend/.venv](backend/.venv): local Python virtual environment (created locally)
- **frontend-web**: web frontend scaffold
- **frontend-mobile**: mobile frontend scaffold
- **sample-songs**: folder for test audio files

**What I implemented / changed (chronological)**
- **Scaffold & files:** created the directory tree and placeholder files for backend, frontends, sample assets.
- **Python venv:** created `backend/.venv` and activated it in the working terminal.
- **Installed packages:** installed audio + web + DB packages into the venv and wrote versions to [backend/requirements.txt](backend/requirements.txt). Key packages: `librosa`, `numpy`, `scipy`, `fastapi`, `uvicorn`, `python-multipart`, `psycopg2-binary`, `sqlalchemy`, `pydantic`, `python-dotenv`.
- **Fingerprint engine:** implemented `AudioFingerprinter` in [backend/app/fingerprint.py](backend/app/fingerprint.py). Features:
  - Audio loading via `librosa`
  - Spectrogram computation (STFT)
  # shazam-clone

  This repository is a scaffold and working prototype for a Shazam-like application (backend + web + mobile). Below is a concise, step-by-step log of what has been created and changed so far, plus commands to reproduce and next recommended steps.

  **Current Structure**
  - **backend**: Python backend service (FastAPI-ready)
    - [backend/app](backend/app): application code
    - [backend/tests](backend/tests): test scripts
    - [backend/.env](backend/.env): environment variables
    - [backend/requirements.txt](backend/requirements.txt): installed packages
    - [backend/.venv](backend/.venv): local Python virtual environment (created locally)
  - **frontend-web**: web frontend scaffold
  - **frontend-mobile**: mobile frontend scaffold
  - **sample-songs**: folder for test audio files

  **What I implemented / changed (chronological)**
  - **Scaffold & files:** created the directory tree and placeholder files for backend, frontends, sample assets.
  - **Python venv:** created `backend/.venv` and activated it in the working terminal.
  - **Installed packages:** installed audio + web + DB packages into the venv and wrote versions to [backend/requirements.txt](backend/requirements.txt). Key packages: `librosa`, `numpy`, `scipy`, `fastapi`, `uvicorn`, `python-multipart`, `psycopg2-binary`, `sqlalchemy`, `pydantic`, `python-dotenv`.
  - **Fingerprint engine:** implemented `AudioFingerprinter` in [backend/app/fingerprint.py](backend/app/fingerprint.py). Features:
    - Audio loading via `librosa`
    - Spectrogram computation (STFT)
    - Peak detection (adaptive threshold)
    - Pair-based hashing and SHA-1 hashes for fingerprints
  - **Tests & diagnostics:** added a runnable test script [backend/tests/test_fingerprint.py](backend/tests/test_fingerprint.py) (functional script, prints debug info). Also added [backend/generate_test_audio.py](backend/generate_test_audio.py) to generate a synthetic `test_song.wav` in `sample-songs/` for testing.
  - **Environment:** created [backend/.env](backend/.env) with PostgreSQL connection example (`DATABASE_URL=postgresql://postgres:changeme@localhost:5432/shazam_clone`) and app settings.
  - **Models:** updated [backend/app/models.py](backend/app/models.py):
    - Renamed `hash` → `hash_value`
    - Fixed string sizes (`String(255)` for metadata, `String(64)` for hashes)
    - Added `created_at` timestamp and composite/indexes for `hash_value`
  - **Database logic:** updated [backend/app/database.py](backend/app/database.py):
    - Connects to DB via SQLAlchemy (`DATABASE_URL` from `.env`)
    - Creates tables with `Base.metadata.create_all()`
    - `add_song()` now inserts fingerprints via `session.add_all(...)` so defaults like `created_at` apply
    - `find_matches()` optimized to fetch all matching hashes in a single DB query, then groups results in memory for scoring

  **Environment & run commands**
  - Create and activate venv (from repo root):
  ```powershell
  Set-Location d:\Project\shazam-clone\backend
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  - Install packages (if you need to re-install):
  ```powershell
  pip install -r requirements.txt
  ```
  - Generate synthetic test audio (creates `sample-songs/test_song.wav`):
  ```powershell
  python generate_test_audio.py
  ```
  - Run the functional fingerprint test script:
  ```powershell
  python tests/test_fingerprint.py
  ```

  **PostgreSQL status**
  - I detected a running PostgreSQL service named `postgresql-x64-18` on the machine. The default `.env` points to `shazam_clone` on `localhost:5432`.

  To create the database and tables (using the `.env` DATABASE_URL):
  ```powershell
  # from backend folder, with venv activated
  python - <<'PY'
  from app.database import DatabaseManager
  # This will create tables if the database exists and connection works
  db = DatabaseManager()
  print('Connected, tables created (if DB exists)')
  PY
  ```

  If the database `shazam_clone` does not exist yet, create it using `psql` or PowerShell (run as user with privileges):
  ```powershell
  # Create database (use your postgres user/password as needed)
  psql -U postgres -c "CREATE DATABASE shazam_clone;"
  ```

  **Notes, known issues & fixes applied**
  - Peak detection originally returned zero peaks because the dB threshold was too high and peak logic was strict. I updated `find_peaks()` to use an adaptive threshold (median + fraction of std dev) and increased the neighborhood size. See [backend/app/fingerprint.py](backend/app/fingerprint.py).
  - Fixed a syntax error that occurred during an earlier edit of `fingerprint.py`.
  - Reconciled `models.py` and `database.py` by renaming `hash` → `hash_value` and updating all database code to use the new column.
  - Replaced `session.bulk_save_objects(...)` with `session.add_all(...)` to ensure model defaults (`created_at`) are applied.
  - Optimized fingerprint lookups to a single DB query using `IN (...)` instead of one query per incoming fingerprint.
  - Replaced Unicode characters in the test script with ASCII-safe markers to avoid PowerShell encoding issues.

— End of change log —
