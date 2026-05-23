# Civic Connect webpage — Vercel deploy folder

**This folder is the live website.** Edit files here and push to GitHub.

## Files Vercel serves

| File | Purpose |
|------|---------|
| `index.html` | Landing page |
| `styles.css` | Styles |
| `test.txt` | Prototype download (primary button) |
| `.nojekyll` | Static hosting helper |
| `vercel.json` | Static site config (no build step) |

## Vercel setup

1. Import repo on [vercel.com](https://vercel.com/new).
2. **Root Directory:** `Civic connect webpage`
3. **Build / Install commands:** empty
4. Deploy

See [VERCEL.md](../VERCEL.md) in the repo root.

## Local preview

```powershell
Set-Location "Civic connect webpage"
python -m http.server 8080
```

Open http://127.0.0.1:8080 — click **Download Civic Connect** to save `test.txt`.

## Later: EXE download

When `CivicConnect.exe` is on GitHub Releases, change the primary button in `index.html` to:

`https://github.com/boluwatifeadewusi5/Grp4-2026-COS102-Project/releases/latest/download/CivicConnect.exe`
