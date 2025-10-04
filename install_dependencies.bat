@echo off
echo Installing LoL Skin Changer dependencies...
echo.

echo Installing Python packages from requirements.txt...
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] All dependencies installed successfully!
    echo.
    echo You can now run the application with:
    echo   python main.py
    echo or
    echo   run_tracer.bat
) else (
    echo.
    echo [ERROR] Failed to install dependencies. Please check the error messages above.
    echo.
    echo Make sure you have Python 3.11+ installed and pip is available.
)

pause
