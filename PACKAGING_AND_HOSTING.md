# Packaging And Free Hosting Guide

This project is still a Tkinter desktop app. The practical free online setup is to host the shared database, source code, documentation, website, and downloadable executable online. The Tkinter window itself still runs on the user's Windows computer.

## 0. Optional Hosted Database

The desktop app supports two database modes:

```text
No environment variable        -> local data file
CIVIC_CONNECT_DATABASE_URL set -> hosted Postgres
```

Recommended free prototype providers:

- Supabase Postgres
- Neon Postgres

Set the connection string before running:

```bash
set CIVIC_CONNECT_DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
python desktop/main.py
```

For PowerShell:

```powershell
$env:CIVIC_CONNECT_DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
python desktop/main.py
```

The app creates the tables automatically and adds starter records only when the `users` table is empty.

Security note: direct database mode is fine for a controlled class presentation, but the connection string can be extracted from a packaged `.exe`. For a public production release, deploy a small API service between the desktop app and the database.

Useful resources:

- Supabase database connection strings: https://supabase.com/docs/reference/postgres/connection-strings
- Neon connection docs: https://neon.com/docs/get-started-with-neon/connect-neon

## 1. Build A Windows EXE Locally

Install the development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Build the app:

```bash
build_windows.bat
```

Output:

```text
dist/CivicConnect.exe
```

The build script uses PyInstaller with:

```bash
pyinstaller --clean --noconfirm --onefile --windowed --name CivicConnect --add-data "rescources;rescources" desktop/main.py
```

Useful resource:

- PyInstaller usage documentation: https://www.pyinstaller.org/en/stable/usage.html

## 2. Build With GitHub Actions

The repository includes:

```text
.github/workflows/windows-build.yml
```

After pushing the project to GitHub, open the Actions tab and run `Build Windows EXE` manually, or push a version tag such as:

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub will build the Windows executable and upload it as a workflow artifact.

Useful resources:

- GitHub Actions Python guide: https://docs.github.com/actions/language-and-framework-guides/using-python-with-github-actions
- GitHub Actions workflow syntax: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## 3. Publish The EXE For Free

Recommended free distribution path:

1. Create a public GitHub repository.
2. Upload this project.
3. Create a GitHub Release.
4. Attach `dist/CivicConnect.exe` to the release.
5. Share the release link.

Useful resource:

- GitHub Releases documentation: https://docs.github.com/github/administering-a-repository/creating-releases

## 4. Add A Free Landing Page

The `docs/` folder contains a GitHub Pages-ready showcase website.

Before publishing:

1. Open `docs/index.html`.
2. Replace every `YOUR_USERNAME/YOUR_REPOSITORY` value with your real GitHub repository path.
3. Push the repository to GitHub.
4. Open `Settings > Pages`.
5. Set the publishing source to the `main` branch and `/docs` folder.

The site showcases the app, explains cloud data mode, and links to the latest release executable.

Useful resources:

- GitHub Pages quickstart: https://docs.github.com/en/pages/quickstart
- Creating a GitHub Pages site: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site

## 5. What "Host Online" Means For Tkinter

Good free options while keeping Tkinter:

- Supabase or Neon for shared hosted Postgres data.
- GitHub repository for source code.
- GitHub Releases for downloadable `.exe` builds.
- GitHub Pages for a public landing/download page.
- SourceForge or itch.io as alternative free download mirrors.

Not recommended if you must keep the same Tkinter UI:

- PythonAnywhere, Render, Railway, and Netlify as the primary app host. These host web apps, not desktop GUI windows.
- Vercel for the **Tkinter window itself** — use Vercel only for the static site in `docs/` (see `VERCEL.md`).
- Replit-style browser IDEs for a public app. Tkinter GUI support is inconsistent and not a true deployment.

If you later need a real browser app, keep the backend and database concepts, then rebuild the UI with Flask/FastAPI plus HTML, or with a frontend framework.
