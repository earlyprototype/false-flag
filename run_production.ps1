Write-Host "=== FALSE FLAG: PRODUCTION LAUNCHER ===" -ForegroundColor Cyan

# 1. Kill Ports 8000 and 3000
function Kill-Port($port) {
    $tcp = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($tcp) {
        Write-Host "Clearing port $port..." -ForegroundColor Yellow
        $tcp | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
}
Kill-Port 8000
Kill-Port 3000

# 2. Start Backend
Write-Host "`n[1/2] Starting Backend API (Port 8000)..."
$backendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k python -m uvicorn api.server:app --port 8000" -PassThru -WindowStyle Normal

# 3. Start Frontend (Production Mode)
Write-Host "`n[2/2] Starting Frontend (Port 3000)..."
Set-Location frontend
# We use 'npm start' which serves the built files. Much faster and stable.
$frontendProcess = Start-Process -FilePath "cmd" -ArgumentList "/k npm start" -PassThru -WindowStyle Normal
Set-Location ..

if ($frontendProcess.Id -and $backendProcess.Id) {
    Write-Host "`nSYSTEM ONLINE" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:3000"
    Write-Host "Backend:  http://localhost:8000"
} else {
    Write-Error "Startup failed."
}


