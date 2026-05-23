# Civic Connect webpage (working copy)

Edit files here during development, then copy changes into **`docs/`** before pushing.

- **GitHub Pages** publishes `/docs` on `main`.
- **Vercel** should use Root Directory **`docs`** (see `VERCEL.md`).

Quick sync from repo root (PowerShell):

```powershell
Copy-Item "Civic connect webpage\index.html" "docs\index.html" -Force
Copy-Item "Civic connect webpage\styles.css" "docs\styles.css" -Force
Copy-Item "Civic connect webpage\test.txt" "docs\test.txt" -Force
```

Deployment instructions: [../docs/README.md](../docs/README.md)
