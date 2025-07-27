@echo off
echo ========================================
echo InsureMyWay Dependency Fix Script
echo ========================================
echo.

echo Checking if virtual environment is activated...
if "%VIRTUAL_ENV%"=="" (
    echo WARNING: Virtual environment not detected!
    echo Please activate your virtual environment first:
    echo   venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo Virtual environment detected: %VIRTUAL_ENV%
echo.

echo ========================================
echo Step 1: Uninstalling problematic packages
echo ========================================
pip uninstall Pillow reportlab -y

echo.
echo ========================================
echo Step 2: Clearing pip cache
echo ========================================
pip cache purge

echo.
echo ========================================
echo Step 3: Upgrading pip
echo ========================================
python -m pip install --upgrade pip

echo.
echo ========================================
echo Step 4: Reinstalling packages
echo ========================================
pip install Pillow
pip install reportlab

echo.
echo ========================================
echo Step 5: Testing installation
echo ========================================
python -c "import PIL; print('✅ PIL/Pillow: OK')" 2>nul || echo "❌ PIL/Pillow: FAILED"
python -c "import reportlab; print('✅ ReportLab: OK')" 2>nul || echo "❌ ReportLab: FAILED"

echo.
echo ========================================
echo Step 6: Running dependency fix script
echo ========================================
python fix_dependencies.py

echo.
echo ========================================
echo Attempting to start the application...
echo ========================================
python app.py

pause
