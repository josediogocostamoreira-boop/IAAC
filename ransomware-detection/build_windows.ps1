$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.13 -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".venv\Scripts\python.exe" -m pip install pyinstaller
& ".venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name RansomwareTrainer `
    src\app.py

Write-Host "Executável criado em dist\RansomwareTrainer.exe"
Write-Host "Mantenha ransom.csv, results e models junto da pasta do projeto."
