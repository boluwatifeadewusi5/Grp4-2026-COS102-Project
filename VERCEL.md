# Vercel — deploy `Civic connect webpage` only

The live site is **`Civic connect webpage/`**. It does **not** run the Tkinter desktop app.

## Required Vercel settings

| Setting | Value |
|--------|--------|
| **Root Directory** | `Civic connect webpage` |
| **Framework Preset** | Other |
| **Build Command** | *(empty)* |
| **Install Command** | *(empty)* |
| **Output Directory** | *(empty — files are at the root of this folder)* |

If you import from the **repository root** instead, the root `vercel.json` sets `outputDirectory` to `Civic connect webpage` — but setting **Root Directory** in the Vercel dashboard is still preferred.

## After changing settings

1. Commit and push `index.html`, `styles.css`, `vercel.json`, and `.nojekyll` in `Civic connect webpage/`.
2. In Vercel → **Deployments** → **Redeploy** (clear build cache if you still see 404).

## URLs that should work

| URL | File |
|-----|------|
| `/` | `index.html` |
| `/styles.css` | `styles.css` |

The **Download Windows EXE** button links to the latest GitHub Release build.

## If the build still fails

- **Root Directory** must match the folder name exactly: `Civic connect webpage` (including spaces).
- Do **not** set Root Directory to `docs` unless you intentionally switch hosts.
- `desktop/main.py` is excluded via `.vercelignore` so Vercel does not treat the repo as a Python web app.

## Desktop app

Ship `CivicConnect.exe` via **GitHub Releases**; the landing page only links to it.
