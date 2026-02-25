Write-Host "=== FALSE FLAG: DEVELOPMENT ENVIRONMENT LAUNCHER ===" -ForegroundColor Cyan

# 1. Check Prerequisites
Write-Host "`n[1/4] Checking Environment..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Write-Error "Python not found!"; exit }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Write-Error "NPM not found!"; exit }
Write-Host "Python and NPM detected." -ForegroundColor Green

# 2. Start Backend
Write-Host "`n[2/4] Starting Backend API (Port 8000)..."
# Using cmd /k to keep window open for errors and ensure correct execution
$backendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k python -m uvicorn api.server:app --port 8000 --reload" -PassThru -WindowStyle Normal
if ($backendProcess.Id) {
    Write-Host "Backend started (PID: $($backendProcess.Id)). Check the new window." -ForegroundColor Green
} else {
    Write-Error "Failed to start backend."
    exit
}

# 3. Start Frontend
Write-Host "`n[3/4] Starting Frontend (Port 3000)..."
Set-Location frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}
# Using cmd /k to keep window open and properly resolve npm
$frontendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k npm run dev" -PassThru -WindowStyle Normal
Set-Location ..
if ($frontendProcess.Id) {
    Write-Host "Frontend started (PID: $($frontendProcess.Id)). Check the new window." -ForegroundColor Green
} else {
    Write-Error "Failed to start frontend."
    Stop-Process -Id $backendProcess.Id -Force
    exit
}

# 4. Wait
Write-Host "`n[4/4] SYSTEM ONLINE" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "`nPress ENTER to stop servers and exit..." -ForegroundColor Yellow
Read-Host

# Cleanup
Write-Host "Stopping servers..."
Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
Write-Host "Shutdown complete."
