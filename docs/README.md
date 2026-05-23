# Civic Connect — GitHub Pages site

This folder is the **published** copy of the landing page. GitHub Pages serves files from `/docs` on the `main` branch.

## Live URL (after Pages is enabled)

https://boluwatifeadewusi5.github.io/Grp4-2026-COS102-Project/

## Deploy checklist

1. Merge these files to `main`.
2. In the repo on GitHub: **Settings → Pages**.
3. Source: **Deploy from a branch**.
4. Branch: **main**, folder: **/docs**.
5. Save and wait for the green deployment message.

## Download button

- **Now:** `test.txt` in this folder (relative link — works on Pages without extra hosting).
- **Later:** Upload `CivicConnect.exe` to [Releases](https://github.com/boluwatifeadewusi5/Grp4-2026-COS102-Project/releases) and set the primary button `href` to:

  `https://github.com/boluwatifeadewusi5/Grp4-2026-COS102-Project/releases/latest/download/CivicConnect.exe`

## Local preview

```bash
cd docs
python -m http.server 8080
```

Open http://127.0.0.1:8080 and click **Download Civic Connect**.
