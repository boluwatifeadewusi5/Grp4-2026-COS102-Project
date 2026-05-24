# Civic Connect - Final Release

Civic Connect is a Python Tkinter desktop app for civic collaboration between Casual Users, NGOs, and Government agencies. The app uses Postgres only for storage, so the same code can run against a hosted database online or a local Postgres server offline.

See [final-release.md](final-release.md) for the latest beta-test fixes.

## Run The App

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

For online shared data, set:

```bash
CIVIC_CONNECT_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
python main.py
```

You can also copy `config.example.json` to `config.json` for local testing. Keep `config.json` private because it can contain database passwords.

For offline use, install Postgres locally, create a database named `civic_connect`, then run:

```bash
python main.py
```

By default, offline mode connects to:

```text
postgresql://postgres:postgres@localhost:5432/civic_connect
```

If your local username, password, host, port, or database name is different, set:

```bash
CIVIC_CONNECT_LOCAL_DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/civic_connect
```

## Refresh

Tkinter screens do not update automatically when another user changes the database. The app no longer rebuilds the active page on a timer; it only refreshes the notification count in the top bar.

The default refresh interval is 15 seconds. You can set any value from 10 to 60 seconds:

```bash
CIVIC_CONNECT_REFRESH_SECONDS=15
python main.py
```

Searches, forms, and scroll position are no longer wiped by automatic full-page refreshes.

Slow hosted database queries are capped by default:

```bash
CIVIC_CONNECT_QUERY_TIMEOUT_MS=5000
```

Connection attempts default to 5 seconds. If the database is unreachable, the app opens a setup/retry screen instead of crashing:

```bash
CIVIC_CONNECT_CONNECT_TIMEOUT_SECONDS=5
```

## Optional Starter Data

Fresh databases do not create sample logins automatically. To load starter records during development, set both values before launching:

```bash
CIVIC_CONNECT_SEED_STARTER_DATA=1
CIVIC_CONNECT_SEED_PASSWORD=choose-a-development-password
python main.py
```

## Features

- Final release fixes organization relations, same-role organization messaging/projects, project CSV downloads, and icon/window branding.
- Beta 1.4.5 opens even when Postgres times out, moves the desktop entrypoint to root `main.py`, and updates packaging.
- Beta 1.4 changes auto-refresh to notification-count refresh only, fixes multi-word search, and adds a Casual Connect tab for following NGO/Government accounts.
- Beta 1.3 adds background database loading, homepage live stats, and heavier lag reduction.
- Postgres-only storage for local and hosted deployments.
- Configurable 10-60 second notification refresh for logged-in screens.
- GitHub Pages-ready showcase/download website in `docs/`.
- Local Iconify/Lucide icon assets in `rescources/`, rendered as PNGs for Tkinter.
- Search posts by topic, body, or author.
- Search suggested Casual Users.
- Casual Users can search and follow NGO/Government public profiles from Connect.
- Search discoverable NGO/Government organizations and relations.
- Filter agreements by status and text.
- Filter projects by status and text.
- Search reports.
- Export dashboard/activity summaries to CSV.
- Upload document records to both agreements and projects.
- Download uploaded project CSV documents when the source file is available on the device.
- Strong backend checks for role separation and accepted relations.

## Core Workflows

Casual Users:

- Create posts
- Like/unlike posts
- Comment on posts
- Add friends
- Accept/reject friend requests
- Follow NGO/Government profiles
- Casual-only messaging
- Notifications
- Profile editing
- CSV export

Government and NGO users:

- Discover NGO and Government organizations
- Send relation requests
- Accept/reject relation requests
- Secure organization messaging after accepted relations
- Create agreements
- Government approval workflow
- Upload document records
- Manage projects
- Submit reports
- Receive notifications
- CSV export

## Package As A Windows EXE

```bash
python -m pip install -r requirements-dev.txt
build_windows.bat
```

The executable will be created at:

```text
dist/CivicConnect.exe
```

You can also run PyInstaller directly:

```bash
python -m PyInstaller --clean --noconfirm --onefile --windowed --name CivicConnect --icon "rescources\app.ico" --add-data "rescources;rescources" main.py
```

## Documentation

All README/setup files now live in `docs/`:

```text
docs/
  README.md
  PROJECT_README.md
  POSTGRES_HOSTING.md
  index.html
  styles.css
```

Use [POSTGRES_HOSTING.md](POSTGRES_HOSTING.md) for the full database hosting walkthrough.
