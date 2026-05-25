# Civic Connect - Upscaled Tkinter Desktop App

Civic Connect is a pure Python desktop app with a functional data layer. It keeps the original Tkinter architecture, while adding stronger validation, safer workflow rules, searchable views, CSV export, and project document management.

## Run

```bash
python desktop/main.py
```

No third-party packages are required for local desktop use. The app uses Python standard library modules including Tkinter, hashlib, secrets, pathlib, csv, and dataclasses.

## Repository layout

| Path | Purpose |
|------|---------|
| `Civic connect webpage/` | **Deploy this** — Vercel landing page and EXE download link |
| `docs/` | Optional GitHub Pages mirror (not used for Vercel) |
| `desktop/` | Desktop app entry (`desktop/main.py`) |

## Publish the website

1. Push to GitHub (use a pull request if `main` is protected).
2. On Vercel, set **Root Directory** to **`Civic connect webpage`**.
3. See [VERCEL.md](VERCEL.md) and [Civic connect webpage/README.md](Civic%20connect%20webpage/README.md).

## Development

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

## Data Storage

The app creates its local data file automatically in the user's app data folder.

If you already ran the older prototype, reset the database before testing the project-document foreign key and new seeded workflow.

## Hosted Database Mode

By default, Civic Connect uses local data. To make all desktop installs share the same hosted database, create a hosted Postgres database on Supabase, Neon, or another Postgres provider, then set:

```bash
CIVIC_CONNECT_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Install cloud database support before running or packaging:

```bash
python -m pip install -r requirements.txt
python desktop/main.py
```

The app will create its tables and starter records if the hosted `users` table is empty.

Important: direct database mode is good for class presentations and controlled prototypes. For a public production app, put a small API between the `.exe` and database so the database password is not bundled into the executable.

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
pyinstaller --clean --noconfirm --onefile --windowed --name CivicConnect --add-data "rescources;rescources" desktop/main.py
```

## Free Distribution And Hosting

Tkinter is a desktop GUI framework, so it cannot be hosted as a normal browser web app without rewriting or wrapping the UI. The free path that keeps this Tkinter code is:

1. Put this folder in a public GitHub repository.
2. Build the `.exe` locally with `build_windows.bat`, or use the included GitHub Actions workflow.
3. Upload `dist/CivicConnect.exe` to a GitHub Release.
4. The download link is in `Civic connect webpage/index.html` (GitHub Releases EXE).
5. Deploy the site on Vercel from `Civic connect webpage/` (see `VERCEL.md`).

See `PACKAGING_AND_HOSTING.md` for step-by-step instructions and links.

## Host the website on Vercel

1. Import the repo on Vercel.
2. Set **Root Directory** to **`Civic connect webpage`**.
3. Leave build/install commands empty.
4. See `VERCEL.md` for details.

The Tkinter app is **not** deployed to Vercel — only the static landing page. Ship the `.exe` via GitHub Releases.

## Project Structure

```text
desktop/main.py
README.md
VERCEL.md
PACKAGING_AND_HOSTING.md
requirements.txt
requirements-dev.txt
build_windows.bat
docs/
  index.html
  styles.css
rescources/
  ICONIFY_SOURCES.txt
  *.svg
  *.png
.github/workflows/windows-build.yml
civic_connect/
  __init__.py
  app.py
  backend.py
  db.py
  icons.py
  theme.py
  ui.py
```

## Notes

This remains a local desktop prototype, not a web deployment. It is designed so the group can present both frontend flows and backend logic without Flask, Django, or external runtime dependencies.
