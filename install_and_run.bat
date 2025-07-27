@echo off
echo ========================================
echo InsureMyWay - Install Dependencies and Run
echo ========================================
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo Activating virtual environment...
    call venv\Scripts\activate
    if errorlevel 1 (
        echo ERROR: Could not activate virtual environment!
        echo Please make sure venv exists or create it with:
        echo   python -m venv venv
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already activated: %VIRTUAL_ENV%
)

echo.
echo ========================================
echo Installing Core Dependencies
echo ========================================

REM Upgrade pip first
python -m pip install --upgrade pip

REM Install core Flask dependencies
pip install Flask==2.3.2
pip install Flask-SQLAlchemy==3.0.5
pip install Flask-Bcrypt==1.0.1
pip install Werkzeug==2.3.6
pip install Flask-Login==0.6.2
pip install Flask-WTF==1.1.1

echo.
echo ========================================
echo Installing ML Dependencies
echo ========================================

pip install numpy==1.24.3
pip install pandas==2.0.3
pip install scikit-learn==1.3.0
pip install scipy==1.11.1
pip install joblib==1.3.1

echo.
echo ========================================
echo Installing Optional PDF Dependencies
echo ========================================

pip install Pillow
pip install reportlab

echo.
echo ========================================
echo Testing Installation
echo ========================================

python -c "import flask; print('✅ Flask: OK')" 2>nul || echo "❌ Flask: FAILED"
python -c "import flask_sqlalchemy; print('✅ Flask-SQLAlchemy: OK')" 2>nul || echo "❌ Flask-SQLAlchemy: FAILED"
python -c "import flask_bcrypt; print('✅ Flask-Bcrypt: OK')" 2>nul || echo "❌ Flask-Bcrypt: FAILED"
python -c "import sklearn; print('✅ Scikit-learn: OK')" 2>nul || echo "❌ Scikit-learn: FAILED"
python -c "import pandas; print('✅ Pandas: OK')" 2>nul || echo "❌ Pandas: FAILED"
python -c "import numpy; print('✅ NumPy: OK')" 2>nul || echo "❌ NumPy: FAILED"

echo.
echo ========================================
echo Starting InsureMyWay Application
echo ========================================

python app.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo Application failed to start!
    echo ========================================
    echo Please check the error messages above.
    echo You can also try running the detailed installer:
    echo   python install_dependencies.py
    pause
)
