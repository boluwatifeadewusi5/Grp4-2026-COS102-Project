# Beta 1.3 - Civic Connect

Beta 1.3 is a Python Tkinter desktop app for civic collaboration between Casual Users, NGOs, and Government agencies. The app uses Postgres only for storage, so the same code can run against a hosted database online or a local Postgres server offline.

See [beta-1.3.md](beta-1.3.md) for the latest background-loading, homepage stats, and heavier performance fixes.

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

Tkinter screens do not update automatically when another user changes the database, so Beta 1.3 refreshes logged-in screens on a timer.

The default refresh interval is 5 seconds. You can set any value from 1 to 5 seconds:

```bash
CIVIC_CONNECT_REFRESH_SECONDS=5
python main.py
```

The app skips auto-refresh while a text field, text box, or dropdown has focus so it does not erase what a user is typing.

Slow hosted database queries are capped by default:

```bash
CIVIC_CONNECT_QUERY_TIMEOUT_MS=5000
```

## Optional Starter Data

Fresh databases do not create sample logins automatically. To load starter records during development, set both values before launching:

```bash
CIVIC_CONNECT_SEED_STARTER_DATA=1
CIVIC_CONNECT_SEED_PASSWORD=choose-a-development-password
python main.py
```

## Features

- Beta 1.3 adds background database loading, homepage live stats, and heavier lag reduction.
- Postgres-only storage for local and hosted deployments.
- Configurable 1-5 second auto-refresh for logged-in screens.
- GitHub Pages-ready showcase/download website in `docs/`.
- Local Iconify/Lucide icon assets in `rescources/`, rendered as PNGs for Tkinter.
- Search posts by topic, body, or author.
- Search suggested Casual Users.
- Search discoverable NGO/Government partners.
- Filter agreements by status and text.
- Filter projects by status and text.
- Search reports.
- Export dashboard/activity summaries to CSV.
- Upload document records to both agreements and projects.
- Strong backend checks for role separation and accepted partnerships.

## Core Workflows

Casual Users:

- Create posts
- Like/unlike posts
- Comment on posts
- Add friends
- Accept/reject friend requests
- Casual-only messaging
- Notifications
- Profile editing
- CSV export

Government and NGO users:

- Discover opposite-side organizations
- Send partner requests
- Accept/reject partner requests
- Secure Government-NGO messaging
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
pyinstaller --clean --noconfirm --onefile --windowed --name CivicConnect --add-data "rescources;rescources" main.py
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
