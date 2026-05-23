@echo off
setlocal
cd /d "%~dp0"

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pyinstaller --clean --noconfirm --onefile --windowed --name CivicConnect --add-data "rescources;rescources" desktop\main.py

echo.
echo Build complete: dist\CivicConnect.exe
