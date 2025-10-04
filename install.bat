@echo off
:: LoL Skin Changer - Windows Installer Launcher
:: This batch file launches the PowerShell installer

echo.
echo ================================================
echo    LoL Skin Changer - Windows Installer
echo ================================================
echo.
echo This installer will automatically download and install:
echo - Python 3.11 (if not already installed)
echo - Tesseract OCR
echo - LoL Skin Changer application
echo - All required dependencies
echo.
echo No user interaction required!
echo.

:: Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell is not available on this system.
    echo Please install PowerShell or use the alternative installer.
    echo.
    echo You can try running: installer_simple.bat
    pause
    exit /b 1
)

:: Run the PowerShell installer
echo Starting installation...
powershell -ExecutionPolicy Bypass -File "%~dp0installer.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Installation completed successfully!
    echo.
    echo You can now start LoL Skin Changer from:
    echo - Desktop shortcut
    echo - Start Menu
    echo - Or run: %LOCALAPPDATA%\LoLSkinChanger\main.py
    echo.
) else (
    echo.
    echo Installation failed. Please check the error messages above.
    echo.
    echo You can try the alternative installer: installer_simple.bat
    echo.
)

pause
