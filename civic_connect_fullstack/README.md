# Civic Connect — Full Working Tkinter + SQLite Codebase

A pure Python desktop prototype with a functional local backend.

## Run

```bash
python main.py
```

No third-party packages are required. It uses only Python standard library modules:
Tkinter, SQLite, hashlib, secrets, pathlib, dataclasses.

## Demo accounts

All passwords are:

```text
password
```

Accounts:

```text
Casual User:      alex@demo.com
NGO:              ngo@demo.com
Government:       gov@demo.com
```

## What works

### Authentication
- Sign up
- Login
- Persistent local accounts
- Password hashing with PBKDF2
- Profile editing

### Role separation
- Casual Users cannot interact with Government or NGO accounts.
- Government and NGO accounts cannot interact with Casual Users.
- Government and NGO users must become accepted partners before messaging or agreements.

### Casual user features
- Create posts
- Like/unlike posts
- Comment on posts
- Add friends
- Accept/reject friend requests
- Casual-only messaging
- Notifications
- Profile editing

### Government and NGO features
- Discover opposite-side organizations
- Send partner requests
- Accept/reject partner requests
- Secure Government-NGO messaging
- Create agreements
- Government approval workflow: approve, reject, request changes
- Upload document records for agreements
- Projects
- Project progress/status updates
- Reports
- Notifications
- Live dashboard counts

## Database

The app creates a SQLite database at:

```text
~/.civic_connect_tkinter/civic_connect.sqlite3
```

To reset demo data, close the app and delete that file, then run the app again.

## Project structure

```text
main.py
README.md
civic_connect/
  __init__.py
  app.py
  backend.py
  db.py
  theme.py
  ui.py
```

## Notes

This is a complete local prototype, not a web deployment. It is designed so your class can demonstrate both the frontend flows and backend logic without needing Flask/Django or external dependencies.
