# Beta 1.4.5 Bug Fixes

Date: May 24, 2026

Beta 1.4.5 focuses on startup stability and packaging correctness after hosted Postgres connection timeouts.

## Bugs Reported

- The app crashed on startup when the configured Neon/Postgres database timed out.
- `main.py` needed to live at the repository root instead of the old `desktop/` folder.
- Packaging still referenced the old `desktop/main.py` entrypoint.
- The branch needed to override the buggy pushed version.

## Fixes Made

- Changed app startup so `CivicBackend()` and the first Postgres connection run in the background after the Tk window opens.
- Added a database setup/retry screen when hosted or local Postgres is unreachable.
- Added a configurable `CIVIC_CONNECT_CONNECT_TIMEOUT_SECONDS` setting with a 5 second default.
- Improved the Postgres connection error message with actionable online/offline setup guidance.
- Moved the tracked entrypoint from `desktop/main.py` to root `main.py`.
- Updated `build_windows.bat` to package from root `main.py`.
- Updated app metadata and documentation to Beta 1.4.5.

## Files Touched

- `main.py`
- `desktop/main.py`
- `build_windows.bat`
- `.github/workflows/windows-build.yml`
- `README.md`
- `PACKAGING_AND_HOSTING.md`
- `VERCEL.md`
- `civic_connect/app.py`
- `civic_connect/db.py`
- `civic_connect/__init__.py`
- `.env.example`
- `docs/beta-1.4.5.md`
- `docs/README.md`
- `docs/PROJECT_README.md`
- `docs/POSTGRES_HOSTING.md`
- `docs/index.html`

## Verification

- Python syntax check passed with `compileall`.
- Import smoke test passed.
- Startup smoke test passed with an intentionally unreachable Postgres URL; the app created the Tk window and closed cleanly instead of crashing.
