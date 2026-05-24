# Postgres Hosting Guide For Beta 1.4.5

Beta 1.4.5 uses Postgres only. The Tkinter app still runs on Windows, while the database can be either:

- Online: a hosted Postgres database such as Supabase or Neon.
- Offline: a Postgres server installed on the same computer.

## 1. Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

`requirements.txt` installs `psycopg`, the Postgres driver used by the app.

## 2. Offline Local Postgres

Use this when you want the app to work without internet.

1. Install PostgreSQL for Windows from `https://www.postgresql.org/download/windows/`.
2. During installation, choose a password for the `postgres` user.
3. Open pgAdmin or SQL Shell.
4. Create a database named `civic_connect`.
5. If your local password is `postgres`, run the app directly:

```bash
python main.py
```

The default offline connection is:

```text
postgresql://postgres:postgres@localhost:5432/civic_connect
```

If your local password or username is different, set this before running:

```powershell
$env:CIVIC_CONNECT_LOCAL_DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/civic_connect"
python main.py
```

Command Prompt version:

```bat
set CIVIC_CONNECT_LOCAL_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/civic_connect
python main.py
```

## 3. Online Hosted Postgres

Use this when multiple desktop installs should share the same data.

Supabase:

1. Create a Supabase project.
2. Open `Project Settings > Database`.
3. Copy a Postgres connection string.
4. Include the correct password and `sslmode=require` if the provider requires it.

Neon:

1. Create a Neon project.
2. Open the connection details.
3. Copy the pooled or direct Postgres connection string.

Then set:

```powershell
$env:CIVIC_CONNECT_DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
python main.py
```

Command Prompt version:

```bat
set CIVIC_CONNECT_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE?sslmode=require
python main.py
```

When `CIVIC_CONNECT_DATABASE_URL` is set, it wins over the local URL.

For local testing, you may copy `config.example.json` to `config.json` and place the same connection string there. Do not commit `config.json`.

## 4. First Run

On first run, the app:

1. Connects to Postgres.
2. Creates the required tables if they do not exist.

Fresh databases start empty. Create accounts through the sign-up screen. For development-only starter records, set both environment variables before first run:

```powershell
$env:CIVIC_CONNECT_SEED_STARTER_DATA="1"
$env:CIVIC_CONNECT_SEED_PASSWORD="choose-a-development-password"
python main.py
```

If the app cannot connect, check:

- The Postgres server is running.
- The database name exists.
- The username and password are correct.
- The provider allows connections from your network.
- Hosted connection strings include required SSL options.

## 5. Refresh Interval

Set the notification refresh interval from 10 to 60 seconds. The default is 15 seconds:

```powershell
$env:CIVIC_CONNECT_REFRESH_SECONDS="15"
python main.py
```

The refresh loop updates only the notification count in the top bar. It no longer rebuilds the active screen, so searches and forms remain usable.

If a hosted database is slow, the app protects the UI with a default query timeout:

```powershell
$env:CIVIC_CONNECT_QUERY_TIMEOUT_MS="5000"
python main.py
```

Connection attempts default to 5 seconds. If the database is unreachable, the app opens a retry/setup screen instead of crashing:

```powershell
$env:CIVIC_CONNECT_CONNECT_TIMEOUT_SECONDS="5"
python main.py
```

## 6. Package As A Windows EXE

Install build dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Build:

```bash
build_windows.bat
```

Output:

```text
dist/CivicConnect.exe
```

For a hosted database, set `CIVIC_CONNECT_DATABASE_URL` on the Windows machine before launching the EXE. Do not hard-code the database password into the source code.

## 7. Free Website Hosting

The `docs/` folder contains the GitHub Pages showcase website.

1. Push the repository to GitHub.
2. Open `Settings > Pages`.
3. Set source to `Deploy from a branch`.
4. Choose the branch and `/docs` folder.
5. Attach `dist/CivicConnect.exe` to a GitHub Release.

The website is only the showcase/download page. The Tkinter app itself still runs on Windows.
