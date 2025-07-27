# PowerShell script to fix pip locks and install dependencies
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "InsureMyWay - Fix and Install Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "WARNING: Virtual environment not detected!" -ForegroundColor Yellow
    Write-Host "Attempting to activate venv..." -ForegroundColor Yellow
    
    if (Test-Path "venv\Scripts\activate.ps1") {
        & "venv\Scripts\activate.ps1"
    } elseif (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    } else {
        Write-Host "ERROR: Could not find virtual environment!" -ForegroundColor Red
        Write-Host "Please create one with: python -m venv venv" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Virtual environment: $env:VIRTUAL_ENV" -ForegroundColor Green
Write-Host ""

# Kill stuck pip processes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Killing stuck processes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    Get-Process -Name "pip" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ Processes killed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ No stuck processes found" -ForegroundColor Yellow
}

Start-Sleep -Seconds 3

# Clear pip cache
Write-Host ""
Write-Host "Clearing pip cache..." -ForegroundColor Yellow
try {
    & python -m pip cache purge
    Write-Host "✅ Cache cleared" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Could not clear cache" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Installing Core Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Function to safely install a package
function Install-Package {
    param(
        [string]$Package,
        [string]$Description
    )
    
    Write-Host ""
    Write-Host "🔧 Installing $Description..." -ForegroundColor Yellow
    
    $maxRetries = 3
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            Write-Host "Attempt $i/$maxRetries : python -m pip install $Package" -ForegroundColor Cyan
            
            $result = & python -m pip install $Package 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Success: $Description" -ForegroundColor Green
                return $true
            } else {
                Write-Host "❌ Failed: $Description" -ForegroundColor Red
                Write-Host "Error: $result" -ForegroundColor Red
                
                if ($i -lt $maxRetries) {
                    Write-Host "⏳ Waiting before retry..." -ForegroundColor Yellow
                    Start-Sleep -Seconds 5
                    
                    # Kill processes again
                    Get-Process -Name "pip" -ErrorAction SilentlyContinue | Stop-Process -Force
                    Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
                    Start-Sleep -Seconds 2
                }
            }
        } catch {
            Write-Host "❌ Exception: $_" -ForegroundColor Red
            if ($i -lt $maxRetries) {
                Start-Sleep -Seconds 5
            }
        }
    }
    
    return $false
}

# Install core dependencies
$corePackages = @(
    @("Flask==2.3.2", "Flask web framework"),
    @("Werkzeug==2.3.6", "WSGI utility library"),
    @("Flask-SQLAlchemy==3.0.5", "Flask SQLAlchemy extension"),
    @("Flask-Bcrypt==1.0.1", "Flask Bcrypt extension"),
    @("Flask-Login==0.6.2", "Flask Login extension"),
    @("Flask-WTF==1.1.1", "Flask WTF forms extension")
)

$failedCore = @()
foreach ($pkg in $corePackages) {
    if (-not (Install-Package -Package $pkg[0] -Description $pkg[1])) {
        $failedCore += $pkg[0]
    }
}

if ($failedCore.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Failed to install core dependencies: $($failedCore -join ', ')" -ForegroundColor Red
    Write-Host "The app will not work without these!" -ForegroundColor Red
    Read-Host "Press Enter to continue anyway"
}

# Install ML dependencies
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Installing ML Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$mlPackages = @(
    @("numpy==1.24.3", "NumPy numerical computing"),
    @("pandas==2.0.3", "Pandas data analysis"),
    @("scikit-learn==1.3.0", "Scikit-learn machine learning"),
    @("scipy==1.11.1", "SciPy scientific computing"),
    @("joblib==1.3.1", "Joblib parallel computing")
)

foreach ($pkg in $mlPackages) {
    Install-Package -Package $pkg[0] -Description $pkg[1] | Out-Null
}

# Install PDF dependencies
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Installing PDF Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Install-Package -Package "Pillow" -Description "PIL image processing" | Out-Null
Install-Package -Package "reportlab" -Description "ReportLab PDF generation" | Out-Null

# Test installation
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 5: Testing Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Test-Import {
    param([string]$Module, [string]$Name)
    
    try {
        & python -c "import $Module; print('✅ $Name: OK')"
        return $true
    } catch {
        Write-Host "❌ $Name: FAILED" -ForegroundColor Red
        return $false
    }
}

$coreWorking = $true
$coreWorking = $coreWorking -and (Test-Import -Module "flask" -Name "Flask")
$coreWorking = $coreWorking -and (Test-Import -Module "flask_sqlalchemy" -Name "Flask-SQLAlchemy")
$coreWorking = $coreWorking -and (Test-Import -Module "flask_bcrypt" -Name "Flask-Bcrypt")

Test-Import -Module "sklearn" -Name "Scikit-learn" | Out-Null
Test-Import -Module "pandas" -Name "Pandas" | Out-Null
Test-Import -Module "numpy" -Name "NumPy" | Out-Null
Test-Import -Module "PIL" -Name "PIL/Pillow" | Out-Null
Test-Import -Module "reportlab" -Name "ReportLab" | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 6: Starting Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($coreWorking) {
    Write-Host "🎉 Core dependencies are working!" -ForegroundColor Green
    Write-Host "🚀 Starting the application..." -ForegroundColor Yellow
    Write-Host ""
    
    & python app.py
} else {
    Write-Host "❌ Core dependencies failed!" -ForegroundColor Red
    Write-Host "Please check the errors above and try manual installation." -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
