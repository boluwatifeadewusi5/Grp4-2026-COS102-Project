# Civic Connect - Upscaled Tkinter Desktop App

Civic Connect is a pure Python desktop app with a functional data layer. It keeps the original Tkinter architecture, while adding stronger validation, safer workflow rules, searchable views, CSV export, and project document management.

## Run

```bash
python main.py
```

No third-party packages are required for local desktop use. The app uses Python standard library modules including Tkinter, hashlib, secrets, pathlib, csv, and dataclasses.

## Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | **Deploy this** — GitHub Pages site (index, styles, `test.txt` download) |
| `Civic connect webpage/` | Working copy of the same site (keep in sync with `docs/` when editing) |
| `app/` | Application / notebook work |

## Publish the website

1. Push to GitHub on branch `main`.
2. **Settings → Pages** → Deploy from branch `main`, folder **`/docs`**.
3. Site URL: https://boluwatifeadewusi5.github.io/Grp4-2026-COS102-Project/

See [docs/README.md](docs/README.md) for download and release details.

## Development

Do not commit `venv/`. A root `.gitignore` excludes virtual environments and common Python artifacts.
