@echo off
echo Starting InsuMyWay Flask Application...
echo.

REM Set the Python path to use Python 3.9
set PYTHONPATH=%CD%\venv\Lib\site-packages

REM Run the application using Python 3.9
py -3.9 app.py

pause
