# Civic Connect — public website

Static landing page for Civic Connect. The **desktop app is not hosted here** — users download the Windows `.exe` from GitHub Releases.

## Deploy on Vercel (recommended)

1. Import the GitHub repo in [Vercel](https://vercel.com/new).
2. **Root Directory:** set to **`docs`** (Project Settings → General). This is the most important step — it stops Vercel from scanning `desktop/main.py` as a Python web app.
3. **Framework Preset:** Other (or leave as detected static).
4. **Build Command / Install Command:** leave empty.
5. Deploy.

If you deploy from the repository root instead of `docs`, the root `vercel.json` sends output from `docs/` and `.vercelignore` excludes Python code — but **Root Directory = `docs` is still preferred.**

Live site files in this folder:

- `index.html` — landing page
- `styles.css` — styles
- `vercel.json` — static site settings
- `package.json` — marks project as static (no Python build)

## Deploy on GitHub Pages

1. Push to GitHub on branch `main`.
2. **Settings → Pages** → Source: branch **`main`**, folder **`/docs`**.
3. Site URL: https://boluwatifeadewusi5.github.io/Grp4-2026-COS102-Project/

## Download button

The primary button links to the latest GitHub Release EXE:

`https://github.com/boluwatifeadewusi5/Grp4-2026-COS102-Project/releases/latest/download/CivicConnect.exe`

Build the EXE with `build_windows.bat` or the GitHub Actions workflow, then attach `CivicConnect.exe` to a release.

## Local preview

```powershell
Set-Location docs
python -m http.server 8080
```

Open http://127.0.0.1:8080
