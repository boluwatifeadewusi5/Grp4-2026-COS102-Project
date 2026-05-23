# Vercel deployment — Civic Connect website only

Vercel hosts the **static webpage** in `docs/`. It does **not** run the Tkinter desktop app.

## Required Vercel settings

| Setting | Value |
|--------|--------|
| Root Directory | **`docs`** |
| Framework Preset | Other |
| Build Command | *(empty)* |
| Install Command | *(empty)* |
| Output Directory | *(empty when Root Directory is `docs`)* |

## Why `app/` was renamed to `desktop/`

Vercel’s Python builder looks specifically for `app/main.py` as a web API entrypoint. This project’s launcher is a **desktop GUI**, not Flask/FastAPI. Renaming `app/` → `desktop/` removes that false match.

## If the build still fails

1. Confirm **Root Directory** is `docs`, not `.`
2. Redeploy after pushing the latest `vercel.json` and `.vercelignore`
3. In the failed deployment, check that no step runs `pip install` or Python functions

## What gets deployed

Only static assets from `docs/`:

- `index.html`
- `styles.css`
- `.nojekyll`

The EXE is distributed via **GitHub Releases**, linked from the download button.
