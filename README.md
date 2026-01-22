  # TuneTrace

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

  ## Populating Database with Music Charts

  The project includes a script to fetch song metadata from music charts and optionally download 30-second preview clips.

  ### Using Deezer API (Recommended - No Auth Required!)
  
  **Deezer API is the recommended option since Spotify API is currently down.**
  
  - ✅ No authentication/credentials needed
  - ✅ 30-second preview clips available
  - ✅ Charts from 15+ countries
  - ✅ ~1200+ songs available

  ```powershell
  # Install required package
  pip install requests

  # Fetch song metadata (Top 200 Global/India + Top 50-100 from 15+ countries)
  python scripts/get_spotify_recommendations.py fetch
  ```
  This creates `music_songs_list.json` and `music_songs_list.csv` with ~1200+ songs.

  ### Download Preview Clips
  ```powershell
  # Download 30-second preview clips
  python scripts/get_spotify_recommendations.py download
  ```
  Preview clips are saved to `music_previews/` directory.

  ### Bulk Upload to Database
  ```powershell
  # Upload all audio files from a directory
  cd backend
  python scripts/reindex_databse.py --audio-dir ../music_previews --force
  ```

  ### Alternative: Spotify API (When Available)
  If Spotify API comes back online, you can use it by:
  1. Get credentials from https://developer.spotify.com/dashboard
  2. Add to `.env`:
  ```env
  SPOTIFY_CLIENT_ID=your_client_id_here
  SPOTIFY_CLIENT_SECRET=your_client_secret_here
  ```
  3. Install: `pip install spotipy`
  4. The script will auto-detect and use Spotify if configured

  ### Using YouTube + yt-dlp (Recommended for Full Songs!)
  
  **Best option for full-length songs instead of 30-second previews.**
  
  - ✅ Full-length songs (not just previews)
  - ✅ No authentication required
  - ✅ Vast catalog (virtually any song on YouTube)
  - ✅ High quality audio extraction
  - ✅ Works with playlists

  ```powershell
  # Install yt-dlp
  pip install yt-dlp

  # Download from a YouTube playlist
  python backend/scripts/download_youtube_songs.py playlist "https://youtube.com/playlist?list=..." 100

  # Download from chart JSON (after running Deezer fetch)
  python backend/scripts/download_youtube_songs.py json 50

  # Search and download a specific song
  python backend/scripts/download_youtube_songs.py search "Artist - Song Title"

  # Interactive mode
  python backend/scripts/download_youtube_songs.py
  ```

  Songs are saved to `youtube_songs/` directory.

  ### Renaming Downloaded Files
  
  To standardize filenames to "Title by Artist" format:
  
  ```powershell
  # Dry run (preview changes)
  python backend/scripts/download_youtube_songs.py rename youtube_songs

  # Execute rename
  python backend/scripts/download_youtube_songs.py rename youtube_songs --execute
  ```

  **Important Notes:**
  - Deezer/Spotify: 30-second preview clips only
  - YouTube: Full songs, better for matching accuracy
  - Preview clips are useful for testing but may not match well with full recordings
  - For full songs from Deezer/Spotify, you'll need to source audio from legal services you subscribe to

  ## Database Management

  ### Clear Database
  
  To delete all songs and fingerprints:
  
  ```powershell
  cd backend
  python scripts/clear_database.py
  ```

  ### Reindex Database
  
  Re-fingerprint all songs with current parameters:
  
  ```powershell
  cd backend
  python scripts/reindex_databse.py --audio-dir ../youtube_songs --force
  ```

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
  - **Performance optimizations:**
    - Switched from `session.add_all()` to `bulk_insert_mappings()` for 10-50x faster fingerprint insertion
    - Removed eager loading (`joinedload`) from `list_songs()` and `get_song()` to dramatically improve query performance
    - Added batching for fingerprint matching queries (1000 hashes per batch)
  - **Fingerprinting parameter tuning:**
    - Reduced `fan_value` from 30 to 5 (was generating 1.3M fingerprints per song)
    - Reduced `target_zone_width` from 250 to 75
    - Reduced `peak_neighborhood_size` to 10 for better peak detection
    - Adjusted peak threshold to 90th percentile (from 98th) for more peaks
    - Target: 30-50k fingerprints per 3-minute song instead of 1.3M
  - **Matching algorithm improvements:**
    - **Threshold progression:** Started at MIN=15 → 10 → 8 → 40 → final dynamic 25% baseline
    - **False positive handling:** Observed false positives at 1-25 matches, true matches at 150+
    - **Dynamic thresholds:** 25% of expected good match (37-38 fingerprints minimum)
    - **Confidence calculation evolution:**
      - Initial: Direct match count
      - V2: (matched / query_fingerprints) * 100 - caused issues with clip length
      - V3: (matched / 15) * 100 - too low baseline
      - Final: (matched / 150) * 100 - aligns with true match range
    - Confidence baseline: 150 matches = 100% confidence
    - Reduces false positives (1-25 range) while catching true matches (150+ range)
  - **Audio preprocessing (optional):**
    - Added optional preprocessing with `preprocess=True` parameter
    - **Trim silence:** Uses `librosa.effects.trim(audio, top_db=20)` to remove quiet sections
    - **Normalize audio:** Uses `librosa.util.normalize(audio)` for consistent volume
    - **Implementation strategy:** Applied ONLY during identification (recordings), NOT during upload
    - **Reasoning:** Uploads stay fast (no preprocessing overhead), recordings get better matching
    - **Performance impact:** Preprocessing adds time but improves accuracy for noisy recordings
  - **Database fixes:**
    - Fixed DetachedInstanceError by adding eager loading initially
    - Later removed eager loading for performance (fingerprints not needed for listing)
    - Balanced between session management and query performance
    - Added optional trim silence and normalization for recordings during identification
    - Preprocessing NOT applied during upload (maintains fast upload speed)
    - Applied only to user recordings for better matching accuracy

  ## Frontend (TuneTrace)
  
  The web frontend has been branded as **TuneTrace** (formerly "Shazam Clone").
  
  ### Running Frontend
  ```powershell
  cd frontend-web
  npm install
  npm run dev -- --host 0.0.0.0 --port 5173
  ```
  
  Access at: http://localhost:5173/
  
  ### Features
  - Audio recording and song identification
  - Song library management (upload, browse, delete)
  - Real-time confidence percentage display
  - Responsive design with React Router navigation

  ## Running Both Servers
  
  ### Backend (FastAPI)
  ```powershell
  cd backend
  $env:PYTHONPATH = 'D:\Project\shazam-clone\backend'
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
  
  ### Frontend (React + Vite)
  ```powershell
  cd frontend-web
  npm run dev -- --host 0.0.0.0 --port 5173
  ```

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
  - 2026-01-21: **Major performance optimizations:**
    - Replaced `session.add_all()` with `bulk_insert_mappings()` for 10-50x faster fingerprint insertion
    - Removed eager loading from `list_songs()` and `get_song()` - dramatically improved query speed
    - Added batching for fingerprint matching queries (1000 hashes per batch) to handle millions of fingerprints
  - 2026-01-21: **Fingerprinting parameter tuning:**
    - Reduced `fan_value` from 30 to 5 and `target_zone_width` from 250 to 75
    - Reduced fingerprint count from 1.3M per song to ~30-50k (sustainable scale)
  - 2026-01-21: **Matching algorithm improvements:**
    - Implemented dynamic thresholds: 25% of expected good match (37-38 minimum fingerprints)
    - Set confidence baseline to 150 matches = 100% confidence
    - Adjusted to reduce false positives (1-25 range) while catching true matches (150+ range)
  - 2026-01-21: **Audio preprocessing implementation:**
    - Added optional preprocessing (trim silence + normalize) for identification recordings
    - Preprocessing NOT applied to uploads to maintain fast upload speed
    - Creates better matching for noisy/variable recordings
  - 2026-01-21: **Music source integration:**
    - Added Deezer API support (no auth required, 30-second previews, 15+ countries)
    - Created YouTube + yt-dlp integration for full-length song downloads
    - Added download scripts with playlist support and search functionality
    - Added file renaming script to standardize format ("Title by Artist")
  - 2026-01-21: **Branding updates:**
    - Renamed frontend from "Shazam Clone" to "TuneTrace"
    - Updated copyright year to 2026
  - 2026-01-21: **Database management tools:**
    - Created `clear_database.py` script for full database reset
    - Updated `reindex_databse.py` with CLI args and better error handling
    - Added `.gitignore` entries for downloaded songs and chart data

  ## Project Statistics (as of 2026-01-21)
  
  - **Backend**: FastAPI with SQLAlchemy ORM, PostgreSQL database
  - **Frontend**: React with Vite, Axios for API calls
  - **Audio Processing**: librosa, NumPy, scipy
  - **Fingerprinting**: Peak-based spectral hashing with configurable parameters
  - **Matching**: Time-delta alignment algorithm with dynamic thresholds
  - **Performance**: ~30-50k fingerprints per 3-minute song, bulk insertion, batched queries
  - **Music Sources**: Deezer API (charts), YouTube + yt-dlp (full songs), Spotify API (legacy)
  - **Scripts**: Song download, renaming, database management, reindexing
  - **Branding**: TuneTrace audio fingerprinting system

  ## Next Steps
  
  **Upcoming Changes:**
  - Database population with downloaded songs from YouTube playlists
  - Bulk fingerprinting and upload of ~1000+ songs across multiple genres
  - Testing and validation of matching accuracy with real-world song database
  - Performance benchmarking with populated database
  - Fine-tuning matching thresholds based on larger dataset

  — End of README
