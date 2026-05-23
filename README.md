# Civic Connect - Upscaled Tkinter + SQLite Prototype

Civic Connect is a pure Python desktop prototype with a functional local backend. It keeps the original Tkinter and SQLite architecture, while adding stronger validation, safer workflow rules, searchable views, CSV export, and project document management.

## Run

```bash
python main.py
```

No third-party packages are required at runtime. The app uses Python standard library modules including Tkinter, SQLite, hashlib, secrets, pathlib, csv, and dataclasses.

## Demo Accounts

All demo passwords are:

```text
password
```

Accounts:

```text
Casual User:      alex@demo.com
NGO:              ngo@demo.com
Government:       gov@demo.com
```

## New In This Upscaled Version

- Optional hosted Postgres database mode through `CIVIC_CONNECT_DATABASE_URL`.
- GitHub Pages-ready showcase/download website in `docs/`.
- Search posts by topic, body, or author.
- Search suggested casual users.
- Search discoverable NGO/Government partners.
- Filter agreements by status and text.
- Filter projects by status and text.
- Search reports.
- Export a user's dashboard/activity summary to CSV.
- Upload document records to both agreements and projects.
- Stronger backend checks for accepted partnerships before organization projects.
- Safer agreement status transitions.
- Friend and partner requests can only be handled while pending.
- Signup validates email format and requires organization names for NGO/Government accounts.
- Placeholder text is no longer saved as real post/agreement/profile content.

## Existing Core Features

### Authentication
- Sign up
- Login
- Persistent local accounts
- Password hashing with PBKDF2
- Profile editing

### Role Separation
- Casual Users cannot interact with Government or NGO accounts.
- Government and NGO accounts cannot interact with Casual Users.
- Government and NGO users must become accepted partners before messaging, agreements, or shared projects.

### Casual User Features
- Create posts
- Like/unlike posts
- Comment on posts
- Add friends
- Accept/reject friend requests
- Casual-only messaging
- Notifications
- Profile editing
- CSV export

### Government and NGO Features
- Discover opposite-side organizations
- Send partner requests
- Accept/reject partner requests
- Secure Government-NGO messaging
- Create agreements
- Government approval workflow: approve, reject, request changes
- Resubmit, activate, and complete agreements through controlled transitions
- Upload document records for agreements and projects
- Projects
- Project progress/status updates
- Reports
- Notifications
- Live dashboard counts
- CSV export

## Database

The app creates a SQLite database at:

```text
~/.civic_connect_tkinter/civic_connect.sqlite3
```

To reset demo data, close the app and delete that file, then run the app again.

If you already ran the older prototype, reset the database before testing the project-document foreign key and new seeded workflow.

## Hosted Database Mode

By default, Civic Connect uses local SQLite. To make all desktop installs share the same hosted database, create a hosted Postgres database on Supabase, Neon, or another Postgres provider, then set:

```bash
CIVIC_CONNECT_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Install cloud database support before running or packaging:

```bash
python -m pip install -r requirements.txt
python main.py
```

The app will create its tables and seed demo accounts if the hosted `users` table is empty.

Important: direct database mode is good for class demos and controlled prototypes. For a public production app, put a small API between the `.exe` and database so the database password is not bundled into the executable.

## Package As A Windows EXE

For local packaging:

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
pyinstaller --clean --noconfirm --onefile --windowed --name CivicConnect main.py
```

## Free Distribution And Hosting

Tkinter is a desktop GUI framework, so it cannot be hosted as a normal browser web app without rewriting or wrapping the UI. The free path that keeps this Tkinter code is:

1. Put this folder in a public GitHub repository.
2. Build the `.exe` locally with `build_windows.bat`, or use the included GitHub Actions workflow.
3. Upload `dist/CivicConnect.exe` to a GitHub Release.
4. Edit `docs/index.html` and replace `YOUR_USERNAME/YOUR_REPOSITORY`.
5. Enable GitHub Pages from the `/docs` folder to publish the showcase/download site.

See `PACKAGING_AND_HOSTING.md` for step-by-step instructions and links.

## Project Structure

```text
main.py
README.md
PACKAGING_AND_HOSTING.md
requirements.txt
requirements-dev.txt
build_windows.bat
docs/
  index.html
  styles.css
.github/workflows/windows-build.yml
civic_connect/
  __init__.py
  app.py
  backend.py
  db.py
  theme.py
  ui.py
```

## Notes

This remains a local desktop prototype, not a web deployment. It is designed so your class can demonstrate both frontend flows and backend logic without Flask, Django, or external runtime dependencies.
