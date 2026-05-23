# Civic Connect — public website (`docs/`)

Static landing page. **Deploy this folder** to Vercel or GitHub Pages. The desktop app is distributed separately as a `.exe`.

## Deploy on Vercel (recommended)

1. Import the repo on [Vercel](https://vercel.com/new).
2. **Root Directory:** **`docs`** (Project Settings → General).
3. **Framework Preset:** Other.
4. **Build Command / Install Command:** leave empty.
5. Deploy.

If deploying from the repository root instead, root `vercel.json` publishes this folder and `.vercelignore` excludes non-website files — but **Root Directory = `docs` is still best.**

See also: [VERCEL.md](../VERCEL.md)

## Deploy on GitHub Pages

1. Push to GitHub on branch `main`.
2. **Settings → Pages** → branch **`main`**, folder **`/docs`**.
3. Live URL: https://boluwatifeadewusi5.github.io/Grp4-2026-COS102-Project/

## Download button

- **Now:** `test.txt` in this folder (`href="test.txt"` on the primary button).
- **Later:** GitHub Release EXE:

  `https://github.com/boluwatifeadewusi5/Grp4-2026-COS102-Project/releases/latest/download/CivicConnect.exe`

## Local preview

```powershell
Set-Location docs
python -m http.server 8080
```

Open http://127.0.0.1:8080 and click **Download Civic Connect**.

## Keep folders in sync

After editing `Civic connect webpage/`, copy into `docs/` before push:

```powershell
Copy-Item "Civic connect webpage\index.html" "docs\index.html" -Force
Copy-Item "Civic connect webpage\styles.css" "docs\styles.css" -Force
Copy-Item "Civic connect webpage\test.txt" "docs\test.txt" -Force
```
