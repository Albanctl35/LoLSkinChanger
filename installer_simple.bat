@echo off
setlocal enabledelayedexpansion

:: LoL Skin Changer - Simple Windows Installer
:: This installer will download and install everything automatically
:: No user interaction required!

echo.
echo ================================================
echo    LoL Skin Changer - Complete Installer
echo ================================================
echo.
echo This installer will automatically download and install:
echo - Python 3.11 (if not already installed)
echo - Tesseract OCR
echo - LoL Skin Changer application
echo - All required dependencies
echo.
echo Please wait while the installation proceeds...
echo.

:: Set installation directory
set "INSTALL_DIR=%LOCALAPPDATA%\LoLSkinChanger"
set "PYTHON_DIR=%LOCALAPPDATA%\Python311"
set "TESSERACT_DIR=%PROGRAMFILES%\Tesseract-OCR"

:: Create installation directory
echo [1/6] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

:: Check if Python is already installed
echo [2/6] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python is already installed.
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
) else (
    echo Python not found. Downloading Python 3.11...
    
    :: Download Python 3.11 installer
    echo Downloading Python 3.11 installer...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe'}"
    
    if not exist "python-installer.exe" (
        echo [ERROR] Failed to download Python installer.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    
    :: Install Python silently
    echo Installing Python 3.11...
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: Wait for installation to complete
    timeout /t 15 /nobreak >nul
    
    :: Clean up installer
    del python-installer.exe
    
    :: Set Python commands
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
)

:: Verify Python installation
echo Verifying Python installation...
%PYTHON_CMD% --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python installation failed.
    pause
    exit /b 1
)

:: Check if Tesseract is already installed
echo [3/6] Checking Tesseract OCR installation...
if exist "%TESSERACT_DIR%\tesseract.exe" (
    echo Tesseract OCR is already installed.
) else (
    echo Tesseract OCR not found. Downloading and installing...
    
    :: Download Tesseract installer
    echo Downloading Tesseract OCR installer...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe' -OutFile 'tesseract-installer.exe'}"
    
    if not exist "tesseract-installer.exe" (
        echo [ERROR] Failed to download Tesseract installer.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    
    :: Install Tesseract silently
    echo Installing Tesseract OCR...
    tesseract-installer.exe /S /D=%TESSERACT_DIR%
    
    :: Wait for installation to complete
    timeout /t 15 /nobreak >nul
    
    :: Clean up installer
    del tesseract-installer.exe
)

:: Verify Tesseract installation
echo Verifying Tesseract installation...
"%TESSERACT_DIR%\tesseract.exe" --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Tesseract installation failed.
    pause
    exit /b 1
)

:: Copy current project files
echo [4/6] Installing application files...
echo Copying LoL Skin Changer files...

:: Copy all project files to installation directory
xcopy "%~dp0*" "%INSTALL_DIR%\" /E /H /Y /I >nul

:: Remove installer files from installation
if exist "%INSTALL_DIR%\installer.bat" del "%INSTALL_DIR%\installer.bat"
if exist "%INSTALL_DIR%\installer_simple.bat" del "%INSTALL_DIR%\installer_simple.bat"

:: Install Python dependencies
echo [5/6] Installing Python dependencies...
cd /d "%INSTALL_DIR%"

:: Upgrade pip first
%PYTHON_CMD% -m pip install --upgrade pip

:: Install dependencies
%PIP_CMD% install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some dependencies may have failed to install.
    echo The application may still work, but some features might be limited.
)

:: Create shortcuts and uninstaller
echo [6/6] Creating shortcuts and uninstaller...

:: Create desktop shortcut
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT_PATH=%DESKTOP%\LoL Skin Changer.lnk"

:: Create VBS script to create shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%SHORTCUT_PATH%" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%PYTHON_CMD%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Arguments = ""%INSTALL_DIR%\main.py"" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "LoL Skin Changer" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript "%TEMP%\CreateShortcut.vbs" >nul
del "%TEMP%\CreateShortcut.vbs"

:: Create start menu entry
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\LoL Skin Changer" mkdir "%START_MENU%\LoL Skin Changer"

:: Create start menu shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateStartMenuShortcut.vbs"
echo sLinkFile = "%START_MENU%\LoL Skin Changer\LoL Skin Changer.lnk" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.TargetPath = "%PYTHON_CMD%" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.Arguments = ""%INSTALL_DIR%\main.py"" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.Description = "LoL Skin Changer" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateStartMenuShortcut.vbs"

cscript "%TEMP%\CreateStartMenuShortcut.vbs" >nul
del "%TEMP%\CreateStartMenuShortcut.vbs"

:: Create uninstaller
(
echo @echo off
echo echo Uninstalling LoL Skin Changer...
echo echo.
echo echo This will remove:
echo echo - LoL Skin Changer application files
echo echo - Desktop shortcut
echo echo - Start menu entry
echo echo.
echo echo Python and Tesseract OCR will NOT be removed.
echo echo.
echo pause
echo.
echo echo Removing application files...
echo if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"
echo.
echo echo Removing shortcuts...
echo if exist "%SHORTCUT_PATH%" del "%SHORTCUT_PATH%"
echo if exist "%START_MENU%\LoL Skin Changer" rmdir /s /q "%START_MENU%\LoL Skin Changer"
echo.
echo echo Uninstallation complete!
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

:: Create run script
(
echo @echo off
echo echo Starting LoL Skin Changer...
echo cd /d "%INSTALL_DIR%"
echo %PYTHON_CMD% main.py %*
echo pause
) > "%INSTALL_DIR%\run.bat"

:: Set Tesseract path in environment
echo Setting up environment variables...
setx TESSERACT_CMD "%TESSERACT_DIR%\tesseract.exe" >nul 2>&1
setx TESSDATA_PREFIX "%TESSERACT_DIR%\tessdata" >nul 2>&1

:: Installation complete
echo.
echo ================================================
echo    Installation Complete!
echo ================================================
echo.
echo LoL Skin Changer has been successfully installed!
echo.
echo Installation location: %INSTALL_DIR%
echo.
echo You can now:
echo 1. Double-click the desktop shortcut to start the application
echo 2. Or run: %INSTALL_DIR%\run.bat
echo 3. Or use the Start Menu entry
echo.
echo To uninstall, run: %INSTALL_DIR%\uninstall.bat
echo.
echo The application will automatically:
echo - Connect to League of Legends
echo - Detect skins during champion select
echo - Inject skins before the game starts
echo.
echo Enjoy your custom skins!
echo.
pause
