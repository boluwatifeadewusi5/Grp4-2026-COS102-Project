# Civic Connect Webpage - Live Site (Vercel)

**Edit files here and push.** This folder is what Vercel deploys.

| File | Purpose |
|------|---------|
| `index.html` | Landing page and EXE download button |
| `CivicConnect.exe` | Bundled Windows executable for direct download |
| `styles.css` | Styles |
| `vercel.json` | Static site config with no build step |
| `.nojekyll` | Static hosting helper |

## Vercel Setup

1. Import the repo on [vercel.com](https://vercel.com/new).
2. **Root Directory:** `Civic connect webpage`
3. **Build / Install commands:** leave empty
4. Deploy

See [VERCEL.md](../VERCEL.md) in the repo root.

## Download Button

Primary button points to the bundled EXE in this deployed folder:

`CivicConnect.exe`

Optional GitHub Releases URL:

`https://github.com/boluwatifeadewusi5/Grp4-2026-COS102-Project/releases/latest/download/CivicConnect.exe`

Build with `build_windows.bat`, then replace this folder's `CivicConnect.exe` and/or attach the EXE to a GitHub Release.

## Local Preview

```powershell
Set-Location "Civic connect webpage"
python -m http.server 8080
```

Open http://127.0.0.1:8080
