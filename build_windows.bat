@echo off
setlocal
cd /d "%~dp0"

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m PyInstaller --clean --noconfirm --onefile --windowed --name CivicConnect --icon "rescources\app.ico" --add-data "rescources;rescources" main.py

echo.
echo Build complete: dist\CivicConnect.exe
