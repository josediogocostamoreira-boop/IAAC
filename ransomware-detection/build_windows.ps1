$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.13 -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível criar o ambiente virtual."
    }
}

& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao instalar as dependências do projeto."
}
& ".venv\Scripts\python.exe" -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao instalar o PyInstaller."
}
& ".venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name RansomwareTrainer `
    src\app.py
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao construir o executável."
}

Write-Host "Executável criado em dist\RansomwareTrainer.exe"
Write-Host "Mantenha ransom.csv, results e models junto da pasta do projeto."
