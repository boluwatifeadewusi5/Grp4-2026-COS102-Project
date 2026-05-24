# Final Release

This release closes the beta-test reports that were still blocking the desktop prototype from feeling complete.

## Reports From Beta Test Users

- Relations did not support all organization-to-organization workflows.
- NGO users could not interact with other NGOs, and Government users could not interact with other Government users.
- Uploaded project CSV files were listed but could not be downloaded from the Projects page.
- Some UI locations still fell back to blank/default icons.
- The app title and branding still looked like a beta build.

## Fixes Made

- Reworked organization relations so NGO-Government, NGO-NGO, and Government-Government accounts can send relation requests, accept them, message, and collaborate on projects.
- Kept formal agreements restricted to one NGO and one Government account because the agreement workflow is still built around government approval.
- Updated the organization sidebar from Partners to Relations.
- Added project CSV download buttons for uploaded `.csv` project documents.
- Added backend permission checks for project-document access before download.
- Added missing Iconify/Lucide `loader-circle` and `refresh-cw` resources.
- Set the app and modal window icon to the transparent gold landmark icon, avoiding the default Tkinter window icon.
- Added `rescources/app.ico` and wired it into PyInstaller so the packaged executable uses the same transparent gold landmark logo.
- Changed the Windows build command to `python -m PyInstaller` so packaging works even when the PyInstaller script is not on PATH.
- Updated release branding to `Final Release`.

## Verification

- Compiled the Python package with `python -m compileall civic_connect main.py`.
- Smoke-tested backend relation behavior for NGO-NGO and Government-Government messaging.
- Smoke-tested project CSV document lookup and access control.
- Built `dist/CivicConnect.exe` with PyInstaller and launched it successfully as `Civic Connect - Final Release`.
