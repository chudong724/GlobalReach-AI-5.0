$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host "=== AI Find Customer - Windows Setup ===" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python 3.11+ and make sure 'python' is on PATH."
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Python virtual environment..."
    Push-Location $Backend
    python -m venv .venv
    Pop-Location
}

Write-Host "Installing backend dependencies..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $Backend "requirements.txt")

$EnvFile = Join-Path $Backend ".env"
$EnvExample = Join-Path $Backend ".env.example"
if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "Created backend/.env from .env.example" -ForegroundColor Yellow
}

$NodeCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $NodeCmd) {
    throw "npm was not found. Install Node.js 18+ first."
}

Write-Host "Installing frontend dependencies..."
Push-Location $Frontend
npm install
Pop-Location

Write-Host "" 
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next: edit backend/.env with your LLM and search API keys, then run deploy/windows/start.ps1"
