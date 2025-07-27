Write-Host "Stopping all Python processes..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process pip* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Write-Host "Starting InsuMyWay Flask Application..." -ForegroundColor Green
Write-Host ""

# Set environment variables
$env:PYTHONPATH = "$PWD\venv\Lib\site-packages"
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Run the application
py -3.9 app.py
