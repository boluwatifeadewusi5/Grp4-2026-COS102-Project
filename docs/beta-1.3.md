# Beta 1.3 Bug Fixes

Date: May 24, 2026

Beta 1.3 is a heavier responsiveness pass. The main goal was to stop Tkinter from freezing during page navigation, searches, and common database actions.

## Bugs Reported

- Pages still lagged heavily and sometimes showed Windows "Not Responding" when clicking buttons.
- Garbage collection needed to be used more deliberately.
- NGO/Government partner search still did not behave well enough.
- The homepage needed live counts for Casual Users, NGOs, Government accounts, and Projects.
- Some app actions caused minor unwanted window resizing.
- The code needed a heavier optimization pass, preferably with a custom Python helper.

## Fixes Made

- Added `civic_connect/performance.py`, a custom Tkinter-safe performance helper that runs database work in a background worker and returns results through `after(...)`.
- Moved heavy screens off the main UI path: Feed, Friends, Profile, Dashboard, Partners, Messages, Agreements, Agreement Detail, Projects, Reports, and Notifications now load through background view tasks.
- Moved common write actions off the UI path: login, signup, posts, likes, comments, friend requests, partner requests, messages, agreement actions, project updates, reports, document uploads, notification read updates, and CSV exports.
- Added stale-view protection so old background loads cannot overwrite a newer screen.
- Added a pending-load guard so auto-refresh does not queue more database work while a screen is still loading.
- Added homepage live stats for Casual Users, NGOs, Government accounts, and Projects.
- Added `public_stats()` and `org_dashboard_snapshot()` backend helpers to fetch screen data in fewer coordinated calls.
- Combined dashboard counters into single-query snapshots to reduce repeated database round-trips during refreshes.
- Added batched project-document loading with `documents_for_projects()` so the Projects page does not query documents once per project.
- Added page limits for friends, partners, conversations, agreements, projects, and reports so Tkinter does not try to render oversized result sets at once.
- Optimized the feed query so like/comment counts are grouped for the visible posts instead of repeated per row.
- Kept widget reads on the main Tkinter thread before background profile updates.
- Added database locking around the shared Postgres connection so background tasks do not collide.
- Kept garbage collection active through the new performance manager after repeated view rebuilds and background actions.
- Reduced layout-driven resizing by preventing the root content frame from propagating child-requested sizes.
- Improved partner search wording and kept the previous `ILIKE` behavior across partner, request, and discovery data.

## Files Touched

- `civic_connect/performance.py`
- `civic_connect/app.py`
- `civic_connect/backend.py`
- `civic_connect/db.py`
- `docs/beta-1.3.md`

## Verification

- Python syntax check passed with `compileall`.
- Full live database testing still requires a configured Postgres database and a runtime with `psycopg` installed.
