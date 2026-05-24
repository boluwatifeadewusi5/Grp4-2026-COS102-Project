# Civic Connect webpage — live site (Vercel)

**Edit files here and push.** This folder is what Vercel deploys.

| File | Purpose |
|------|---------|
| `index.html` | Landing page (EXE download button) |
| `styles.css` | Styles |
| `vercel.json` | Static site config (no build step) |
| `.nojekyll` | Static hosting helper |

## Vercel setup

1. Import the repo on [vercel.com](https://vercel.com/new).
2. **Root Directory:** `Civic connect webpage`
3. **Build / Install commands:** leave empty
4. Deploy

See [VERCEL.md](../VERCEL.md) in the repo root.

## Download button

Primary button → latest release EXE:

`https://github.com/boluwatifeadewusi5/beta-1.0/releases/latest/download/CivicConnect.exe`

Build with `build_windows.bat` or the GitHub Actions workflow, then attach `CivicConnect.exe` to a release.

## Local preview

```powershell
Set-Location "Civic connect webpage"
python -m http.server 8080
```

Open http://127.0.0.1:8080
