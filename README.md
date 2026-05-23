# Grp4-2026-COS102-Project — Civic Connect

COS102 group project: Civic Connect desktop prototype and public landing page.

## Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | **Deploy this** — live site for Vercel / GitHub Pages |
| `Civic connect webpage/` | Working copy — sync into `docs/` before you push |
| `app/` | Local app / notebook work (not deployed to Vercel) |

## Host the website on Vercel

1. Push the latest code to GitHub.
2. Import the repo on [Vercel](https://vercel.com/new).
3. Set **Root Directory** to **`docs`**.
4. Leave **Build Command** and **Install Command** empty.
5. Deploy.

Details: [VERCEL.md](VERCEL.md) and [docs/README.md](docs/README.md).

The Tkinter app is **not** hosted on Vercel — only this static landing page. Ship the `.exe` via GitHub Releases when ready.

## Host on GitHub Pages

1. Push to branch `main`.
2. **Settings → Pages** → branch **`main`**, folder **`/docs`**.
3. https://boluwatifeadewusi5.github.io/Grp4-2026-COS102-Project/

## Development

Do not commit `venv/`. Root `.gitignore` excludes virtual environments.

After editing the site in `Civic connect webpage/`, sync files into `docs/` (see `docs/README.md`) before pushing.
