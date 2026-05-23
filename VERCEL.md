# Vercel — deploy `Civic connect webpage` only

The live site is **`Civic connect webpage/`**, not `docs/`.

## Required Vercel project settings

| Setting | Value |
|--------|--------|
| **Root Directory** | `Civic connect webpage` |
| **Framework Preset** | Other |
| **Build Command** | *(empty)* |
| **Install Command** | *(empty)* |
| **Output Directory** | *(empty — files are already at the root of this folder)* |

## After changing settings

1. Commit and push all files in `Civic connect webpage/` (`index.html`, `styles.css`, `test.txt`, `vercel.json`, `.nojekyll`).
2. In Vercel → **Deployments** → **Redeploy** (use “Redeploy with existing Build Cache” **cleared** if you still see 404).

## URLs that should work

| URL | File |
|-----|------|
| `/` | `index.html` |
| `/test.txt` | `test.txt` (download button) |
| `/styles.css` | `styles.css` |

## If you still get 404

- **Root Directory** must be exactly `Civic connect webpage` (match the folder name on GitHub, including spaces).
- Do **not** set Output Directory to `docs`.
- Remove `app/main.py` from the repo if it was re-added — it makes Vercel treat the project as Python.

## Desktop app

The Tkinter app is **not** on Vercel. Ship `CivicConnect.exe` via GitHub Releases; the site only links to it later.
