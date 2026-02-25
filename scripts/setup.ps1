param(
  [string]$PythonExe = "python"
)

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $PythonExe -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running gate runner..." -ForegroundColor Cyan
& $PythonExe scripts/gate_runner.py
exit $LASTEXITCODE
