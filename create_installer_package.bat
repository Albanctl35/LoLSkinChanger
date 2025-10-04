@echo off
:: Create a distributable installer package for LoL Skin Changer
:: This script creates a complete installer package that can be distributed

echo.
echo ================================================
echo    Creating LoL Skin Changer Installer Package
echo ================================================
echo.

:: Set package directory
set "PACKAGE_DIR=LoLSkinChanger_Installer"
set "PACKAGE_ZIP=LoLSkinChanger_Installer.zip"

:: Create package directory
echo [1/4] Creating package directory...
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

:: Copy installer files
echo [2/4] Copying installer files...
copy "installer_complete.bat" "%PACKAGE_DIR%\install.bat"
copy "installer_simple.bat" "%PACKAGE_DIR%\installer_simple.bat"
copy "installer.ps1" "%PACKAGE_DIR%\installer.ps1"
copy "INSTALLER_README.md" "%PACKAGE_DIR%\README.md"

:: Copy application files
echo [3/4] Copying application files...
xcopy "main.py" "%PACKAGE_DIR%\" /Y
xcopy "requirements.txt" "%PACKAGE_DIR%\" /Y
xcopy "README.md" "%PACKAGE_DIR%\APP_README.md" /Y
xcopy "database" "%PACKAGE_DIR%\database\" /E /I
xcopy "lcu" "%PACKAGE_DIR%\lcu\" /E /I
xcopy "ocr" "%PACKAGE_DIR%\ocr\" /E /I
xcopy "state" "%PACKAGE_DIR%\state\" /E /I
xcopy "threads" "%PACKAGE_DIR%\threads\" /E /I
xcopy "utils" "%PACKAGE_DIR%\utils\" /E /I
xcopy "injection" "%PACKAGE_DIR%\injection\" /E /I
xcopy "dependencies" "%PACKAGE_DIR%\dependencies\" /E /I

:: Create package info file
echo [4/4] Creating package info...
(
echo LoL Skin Changer - Complete Windows Installer Package
echo =====================================================
echo.
echo This package contains everything needed to install
echo LoL Skin Changer on Windows systems.
echo.
echo Files included:
echo - install.bat (Main installer - USE THIS!)
echo - installer_simple.bat (Alternative installer)
echo - installer.ps1 (PowerShell installer)
echo - README.md (Installation instructions)
echo - Complete application files
echo.
echo Installation:
echo 1. Extract this ZIP file
echo 2. Double-click install.bat
echo 3. Wait for installation to complete
echo 4. Done!
echo.
echo The installer will automatically:
echo - Download and install Python 3.11
echo - Download and install Tesseract OCR
echo - Install the LoL Skin Changer application
echo - Install all required dependencies
echo - Create desktop and start menu shortcuts
echo.
echo No user interaction required!
echo.
echo For support, see README.md
) > "%PACKAGE_DIR%\PACKAGE_INFO.txt"

:: Create ZIP package
echo Creating ZIP package...
powershell -Command "& {Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%PACKAGE_ZIP%' -Force}"

:: Clean up
rmdir /s /q "%PACKAGE_DIR%"

echo.
echo ================================================
echo    Package Created Successfully!
echo ================================================
echo.
echo Package file: %PACKAGE_ZIP%
echo.
echo This package contains:
echo - Complete installer (install.bat)
echo - Alternative installer (installer_simple.bat)
echo - PowerShell installer (installer.ps1)
echo - Installation instructions (README.md)
echo - Complete LoL Skin Changer application
echo.
echo To distribute:
echo 1. Share the %PACKAGE_ZIP% file
echo 2. Users extract it and run install.bat
echo 3. Installation is completely automatic!
echo.
echo The installer will handle everything:
echo - Download Python 3.11
echo - Download Tesseract OCR
echo - Install the application
echo - Create shortcuts
echo - Set up environment
echo.
echo No user interaction required!
echo.
pause
