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

## Avoid the Python error

If Vercel reports:

`Found app/main.py but it does not export a top-level "app"...`

that means it is trying to deploy Python code, not the website. Fix it by setting **Root Directory** to **`docs`**, or ensure `app/main.py` does not exist in the branch you deploy.

## Deploy steps

1. Push this repository to GitHub.
2. Import the repo on [Vercel](https://vercel.com/new).
3. Set **Root Directory** to **`docs`**.
4. Leave build and install commands empty.
5. Deploy.

## Download button

The site serves `test.txt` from this folder for prototype testing. When the Windows `.exe` is ready, upload it to GitHub Releases and update the primary button `href` in `docs/index.html` (see `docs/README.md`).
