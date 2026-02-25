Write-Host "=== CLEANUP & LAUNCH ===" -ForegroundColor Cyan

# 1. Kill Ports 8000 and 3000
Write-Host "Checking for existing processes..."

# Function to kill process by port
function Kill-Port($port) {
    $tcp = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($tcp) {
        Write-Host "Found process on port $port. Killing..." -ForegroundColor Yellow
        $tcp | ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Port $port cleared." -ForegroundColor Green
    } else {
        Write-Host "Port $port is free." -ForegroundColor Gray
    }
}

Kill-Port 8000
Kill-Port 3000

# 2. Run verify_and_run.ps1
Write-Host "`nStarting verify_and_run.ps1..."
./verify_and_run.ps1


