# Beta 1.4 Bug Fixes

Date: May 24, 2026

Beta 1.4 focuses on making the app usable during normal navigation and search. The biggest change is that timed refreshes no longer rebuild the whole screen.

## Bugs Reported

- Auto-refresh happened too often and made the app hard to use.
- Search still did not reliably return the expected records.
- Casual users needed a Connect tab showing only NGO and Government accounts they can follow.

## Fixes Made

- Changed auto-refresh from full-page reloads to notification-count refresh only.
- Increased `CIVIC_CONNECT_REFRESH_SECONDS` to a safer 10-60 second range, with a 15 second default.
- Added a top-bar alert text variable so notification counts can update without destroying the active page.
- Added a Postgres `follows` table for casual-to-organization follows.
- Added backend follow/unfollow methods that only allow Casual Users to follow NGO and Government accounts.
- Added `connect_accounts()` to return followed and discoverable NGO/Government profiles.
- Added a new Casual `Connect` tab with search, Follow, and Unfollow actions.
- Added multi-word search matching across names, emails, organizations, locations, bios, roles, statuses, titles, and body text where appropriate.
- Applied Friends search to friends, incoming requests, outgoing requests, and suggested users instead of suggested users only.
- Added empty-state text so a filtered section clearly shows when no records match.
- Added Enter-key search support on the feed search field.
- Updated casual dashboard metrics to show how many NGO/Government accounts the user follows.

## Files Touched

- `civic_connect/app.py`
- `civic_connect/backend.py`
- `civic_connect/db.py`
- `civic_connect/__init__.py`
- `.env.example`
- `docs/beta-1.4.md`
- `docs/README.md`
- `docs/PROJECT_README.md`
- `docs/POSTGRES_HOSTING.md`
- `docs/index.html`

## Verification

- Python syntax check passed with `compileall`.
- Import smoke test passed.
- Backend placeholder smoke tests passed for casual and organization search queries.
- Full live database testing still requires a configured Postgres database and a runtime with `psycopg` installed.
