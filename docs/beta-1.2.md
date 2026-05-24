# Beta 1.2 Bug Fixes

Date: May 24, 2026

Beta 1.2 focuses on app responsiveness, smoother casual-user interactions, better window resizing, working organization search, and cleaner branding.

## Bugs Reported

- Casual users experienced heavy lag when liking, commenting, adding friends, messaging, or interacting with other users.
- The app could show Windows "Not Responding" during heavier refresh or database work.
- Opening the landing page from a logged-in workspace looked like it logged the user out.
- Old "Beta 1.0" labels were still visible inside the app.
- The app window was difficult to resize because the minimum size was too large and some screens were too rigid.
- NGO and Government search did not work reliably.
- Performance needed garbage collection support.

## Fixes Made

- Replaced per-post comment loading with one batched `recent_comments_for_posts` query.
- Reduced feed rendering from 80 posts to 40 posts per refresh to keep the UI responsive.
- Limited message loading to the latest 120 messages per conversation.
- Added more Postgres indexes for feed, comments, likes, users, and message-heavy screens.
- Added an 8 second Postgres connection timeout and configurable 5 second query timeout through `CIVIC_CONNECT_QUERY_TIMEOUT_MS`.
- Changed search filters from case-sensitive `LIKE` to Postgres `ILIKE`.
- Fixed NGO/Government partner search so it filters accepted partners, incoming requests, outgoing requests, and discoverable organizations.
- Added refresh throttling so auto-refresh waits briefly after clicks or typing.
- Added periodic idle-time garbage collection after repeated screen rebuilds.
- Fixed the landing/about page so logged-in users stay logged in and see workspace/profile actions instead of login/signup.
- Replaced in-app "Beta 1.0" labels with the `Civic Connect` brand name and updated the window title to `Civic Connect - Beta 1.2`.
- Lowered the app minimum size and made the landing page stack its hero sections on narrower windows.
- Scoped mouse-wheel bindings to the active scroll area so old destroyed scroll views do not keep stale global bindings.

## New Config Option

```bash
CIVIC_CONNECT_QUERY_TIMEOUT_MS=5000
```

Set it to a higher value for slow hosted databases, or set it to `0` to disable the query timeout.

## Verification

- Python syntax check passed with `compileall`.
- Full live database testing still requires a local or hosted Postgres connection with `psycopg` installed in the runtime.
