# Beta 1.1 Release Notes

Date: May 23, 2026

Beta 1.1 focuses on stability, Postgres performance, safer configuration, and cleaner release documentation.

## Fixed

- Fixed the Messages screen Postgres error: `column "last_at" does not exist`.
- Replaced the conversation ordering query with a Postgres-safe `LEFT JOIN LATERAL` query.
- Removed automatic starter/demo login creation from normal app startup.
- Fixed a text encoding issue in starter message content.

## Optimized

- Reused a single Postgres connection instead of opening and closing a new connection for every query.
- Added indexes for messages, friendships, partner requests, conversations, and reports.
- Changed dashboard summary counts to use `COUNT(*)` queries instead of loading full lists.
- Changed the default auto-refresh interval to 5 seconds while still allowing 1 to 5 seconds with `CIVIC_CONNECT_REFRESH_SECONDS`.
- Added clean database connection shutdown when the Tkinter window closes.

## Security And Config

- Removed tracked `config.json` files from Git so database credentials are not pushed.
- Added `config.example.json` as a safe template.
- Updated `.gitignore` so real local config files stay private.
- Starter data now requires both:

```bash
CIVIC_CONNECT_SEED_STARTER_DATA=1
CIVIC_CONNECT_SEED_PASSWORD=choose-a-development-password
```

## How To Use Beta 1.1

1. Pull the latest `beta-1.0` branch.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Set `CIVIC_CONNECT_DATABASE_URL` for hosted Postgres or `CIVIC_CONNECT_LOCAL_DATABASE_URL` for a local Postgres server.
4. Run `python main.py`.

## Verification

- Python syntax check passed with `compileall`.
- Full app launch was not verified in the Codex runtime because that runtime did not have `psycopg` installed or a reachable Postgres database configured.
