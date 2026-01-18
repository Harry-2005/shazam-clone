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
  - **FastAPI API layer:** wired [backend/app/main.py](backend/app/main.py) and [backend/app/api/routes.py](backend/app/api/routes.py) with `/api/v1` router, upload/identify/song CRUD/stats/health endpoints, CORS enabled, temp-file handling, and Pydantic schemas for request/response validation.
  - **API correctness fixes:** adjusted identification/upload flows to return structured Pydantic responses, cleaned temp file handling, included confidence percentages, and ensured song lookups return full metadata—this resolved the incorrect/empty outputs we were seeing from `/identify` and song endpoints.
  - **Web API client:** added Axios service [frontend-web/src/services/api.js](frontend-web/src/services/api.js) covering song upload/list/detail/delete, identify, stats, and health against `http://localhost:8000/api/v1`.
  - **Web UI scaffold:** set up React Router navigation in [frontend-web/src/App.js](frontend-web/src/App.js); built Home page (stats + feature cards), Identify flow (recorder stub + identifying spinner + result display), and SongList component to browse/delete songs from the API; Upload/Library/file upload/recorder components are scaffolded for future work.
  - **Frontend dependency:** installed `@fortawesome/fontawesome-free` in `frontend-web` for icon support.

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

  ## Structure
  - [backend](backend): Python backend service (FastAPI-ready)
    - [backend/app](backend/app): application code
    - [backend/tests](backend/tests): test scripts
    - [backend/requirements.txt](backend/requirements.txt): pinned dependencies
    - [backend/.venv](backend/.venv): local Python virtual environment (created locally)
  - [frontend-web](frontend-web)
  - [frontend-mobile](frontend-mobile)
  - [sample-songs](sample-songs): test audio files

  ## Quick setup (backend)
  1. Open PowerShell and go to the backend folder:
  ```powershell
  Set-Location D:\Project\shazam-clone\backend
  ```
  2. Activate the existing venv (or use the venv python directly):
  ```powershell
  .# Activate (PowerShell)
  .\.venv\Scripts\Activate.ps1
  # or run commands using the venv python explicitly:
  .venv\Scripts\python -m pip install -r requirements.txt
  ```
  3. Install / reinstall requirements (if needed):
  ```powershell
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\python -m pip install -r requirements.txt
  ```
  4. Verify `SQLAlchemy` is available:
  ```powershell
  .venv\Scripts\python -c "import sqlalchemy; print(sqlalchemy.__version__)"
  ```

  ## Running tests
  - Important: run tests using the backend venv Python and from `backend/tests` so the `app` package imports correctly.
  ```powershell
  Set-Location D:\Project\shazam-clone\backend\tests
  D:\Project\shazam-clone\backend\.venv\Scripts\python test_database.py
  ```
  - Notes:
    - `tests/test_database.py` expects a test audio file at `sample-songs/test_song.mp3` (relative to repository root). Provide one or generate a synthetic test file.
    - The test is an integration-style script (prints diagnostic output). For automated CI, convert to pytest-style assertions or mock external dependencies.

  ## Database
  - The backend uses SQLAlchemy with the database URL from `backend/.env` (`DATABASE_URL`). Example:
  ```
  DATABASE_URL=postgresql://postgres:changeme@localhost:5432/shazam_clone
  ```
  - For quick local testing you can use SQLite instead (no Postgres required):
  ```powershell
  setx DATABASE_URL "sqlite:///./test.db"
  ```

  ### Sequences / IDs
  - PostgreSQL sequences continue incrementing across inserts/deletes and failed transactions. If you see inserted rows with `id > 1` despite an empty table, that's expected.
  - To reset IDs in tests or dev DB (Postgres):
  ```sql
  TRUNCATE songs RESTART IDENTITY CASCADE;
  -- or to set sequence to max(id):
  SELECT setval(pg_get_serial_sequence('songs','id'), COALESCE((SELECT MAX(id) FROM songs), 0));
  ```

  ## Recent fixes and notes
  - Reinstalled pinned requirements into `backend/.venv`.
  - Fixed psycopg2 insertion error caused by `numpy.int64` time offsets: `app/database.py` now casts fingerprint offsets to `int` before inserting.
  - Added guidance to run tests using the venv Python so imports like `app` and packages such as `SQLAlchemy` resolve correctly.

  ## Troubleshooting
  - No module named 'sqlalchemy': activate the venv or invoke `.venv\Scripts\python`.
  - No module named 'app': run tests from `backend/tests` or set `PYTHONPATH` to include `backend`, or install the package in editable mode (`pip install -e .`) if you create packaging files.
  - Database connection errors: ensure `DATABASE_URL` points to a running Postgres or switch to SQLite for quick tests.

  ## Log Notes

  - 2026-01-08: Reinstalled pinned requirements into `backend/.venv` (force-reinstall). Verified `SQLAlchemy` installed.
  - 2026-01-08: Fixed insertion error caused by `numpy.int64` time offsets by casting offsets to `int` in `app/database.py`.
  - 2026-01-08: Confirmed tests must be run using the backend venv Python and from `backend/tests` so the `app` package imports correctly; guidance added earlier.
  - 2026-01-08: Observed PostgreSQL sequence behavior — empty tables can still produce non-1 autoincrement IDs; added `TRUNCATE ... RESTART IDENTITY` guidance.
  - 2026-01-18: Added FastAPI router + endpoints (upload/identify/songs/stats/health) with CORS and schema validation; ensured `/api/v1` prefix and health root wiring.
  - 2026-01-18: Fixed API responses and temp-file handling so `/identify` returns full song metadata with confidence metrics and song endpoints stop returning empty/incorrect payloads.
  - 2026-01-18: Created web API client service, React Router shell, Home/Identify pages, SongList component hooked to the API, and installed `@fortawesome/fontawesome-free` for UI icons.

  — End of README
