# Civic Connect webpage — working copy

Edit files here during development, then copy changes into **`docs/`** before pushing.

- **GitHub Pages** publishes `/docs` on `main`.
- **Vercel** should use Root Directory **`docs`** (see [VERCEL.md](../VERCEL.md)).

## Sync to `docs/` before push

```powershell
Copy-Item "Civic connect webpage\index.html" "docs\index.html" -Force
Copy-Item "Civic connect webpage\styles.css" "docs\styles.css" -Force
Copy-Item "Civic connect webpage\test.txt" "docs\test.txt" -Force
```

## Files in this folder

| File | Purpose |
|------|---------|
| `index.html` | Landing page |
| `styles.css` | Styles |
| `test.txt` | Prototype download (local testing) |
| `.nojekyll` | Static hosting helper |
| `vercel.json` | Static site config (used only if this folder is the Vercel root) |

## Local preview

```powershell
Set-Location "Civic connect webpage"
python -m http.server 8080
```

Open http://127.0.0.1:8080

## Deploy

- **Vercel:** Root Directory = **`docs`** — see [VERCEL.md](../VERCEL.md)
- **GitHub Pages:** folder **`/docs`** on branch **`main`**

The download button in `docs/index.html` links to the latest GitHub Release EXE.
