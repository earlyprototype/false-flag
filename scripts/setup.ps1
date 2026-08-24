param(
  [string]$PythonExe = "python"
)

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $PythonExe -m pip install -q -r requirements.txt
exit $LASTEXITCODE
