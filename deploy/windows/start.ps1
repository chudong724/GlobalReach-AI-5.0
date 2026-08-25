$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Backend virtual environment not found. Run deploy/windows/setup.ps1 first."
}

if (-not (Test-Path (Join-Path $Backend ".env"))) {
    throw "backend/.env not found. Run setup.ps1 and configure API keys first."
}

Write-Host "Starting 文美全球AI获客系统..." -ForegroundColor Cyan

$backendArgs = @(
    "-m", "uvicorn", "branded_app:app",
    "--host", "127.0.0.1",
    "--port", "8000"
)

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Backend'; & '$VenvPython' $($backendArgs -join ' ')"
)

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Frontend'; npm run dev"
)

Write-Host "Backend: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Swagger: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
