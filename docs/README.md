# docs/ — mirror only (not used for Vercel)

The **deployed website** is in **`Civic connect webpage/`**.

Vercel and this project use that folder as the public site. `docs/` is kept for optional GitHub Pages (`/docs` on `main`) if you enable it separately.

To sync from the live folder:

```powershell
Copy-Item "Civic connect webpage\index.html" "docs\index.html" -Force
Copy-Item "Civic connect webpage\styles.css" "docs\styles.css" -Force
Copy-Item "Civic connect webpage\test.txt" "docs\test.txt" -Force
```

Vercel instructions: [VERCEL.md](../VERCEL.md)
