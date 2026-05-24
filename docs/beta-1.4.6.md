# Beta 1.4.6

Beta 1.4.6 focuses on getting the desktop build running when the hosted Neon endpoint accepts TCP traffic but fails the Postgres handshake.

## Bugs Fixed

- The app could still stop at the database screen when a hosted Postgres URL was present but unreachable from the current network.
- A bad or blocked hosted URL prevented offline/local Postgres from being tried.
- The database setup screen still pointed users at manual local setup instead of the project recovery script.
- The visible app version still showed Beta 1.4.5.

## Changes Made

- Added database connection fallback order:
  - configured hosted `CIVIC_CONNECT_DATABASE_URL`
  - configured `CIVIC_CONNECT_LOCAL_DATABASE_URL`
  - default local Postgres on port `5432`
  - recovery local Postgres on port `55432`
- Added password masking for attempted database URLs in connection errors.
- Added `scripts/start_local_postgres.ps1`, which initializes a user-owned local Postgres cluster, creates the `civic_connect` database, starts it on port `55432`, and writes a private `config.json`.
- Added `.local-postgres/` to `.gitignore` so local database files are never committed.
- Updated `config.example.json` to show the offline local Postgres option safely.
- Updated the app version to Beta 1.4.6.

## Verification

- Created and tested a local Postgres database at `127.0.0.1:55432`.
- Confirmed the Python backend initializes its Postgres schema successfully against the local database.
- Created a fresh Neon recovery branch/endpoint and tested the generated URI. It failed with the same pre-authentication Postgres protocol timeout, confirming the immediate blocker is outside the Tkinter app code.

## Notes

- The hosted Neon connection should be retested from another network or after Neon support confirms endpoint health.
- Until then, the desktop app can run on local Postgres without SQLite or any non-Postgres database.
