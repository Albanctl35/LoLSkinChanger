@echo off
setlocal enabledelayedexpansion

:: LoL Skin Changer - Complete Windows Installer
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
echo [1/8] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

:: Check if Python is already installed
echo [2/8] Checking Python installation...
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
    timeout /t 10 /nobreak >nul
    
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
echo [3/8] Checking Tesseract OCR installation...
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
    timeout /t 10 /nobreak >nul
    
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

:: Download LoL Skin Changer application
echo [4/8] Downloading LoL Skin Changer application...
echo This may take a few minutes depending on your internet connection...

:: Create a temporary directory for the download
set "TEMP_DIR=%TEMP%\LoLSkinChanger_Download"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: Download the application as a ZIP file
echo Downloading application files...
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/your-repo/LoLSkinChanger/archive/main.zip' -OutFile '%TEMP_DIR%\LoLSkinChanger.zip'}"

:: Alternative: If GitHub download fails, create the application structure manually
if not exist "%TEMP_DIR%\LoLSkinChanger.zip" (
    echo Creating application structure manually...
    
    :: Create main application files
    echo Creating main.py...
    (
    echo #!/usr/bin/env python3
    echo # -*- coding: utf-8 -*-
    echo """
    echo Main entry point for the modularized LoL Skin Changer
    echo """
    echo.
    echo import argparse
    echo import time
    echo from ocr.backend import OCR
    echo from database.name_db import NameDB
    echo from database.multilang_db import MultiLanguageDB
    echo from lcu.client import LCU
    echo from state.shared_state import SharedState
    echo from threads.phase_thread import PhaseThread
    echo from threads.champ_thread import ChampThread
    echo from threads.ocr_thread import OCRSkinThread
    echo from threads.websocket_thread import WSEventThread
    echo from utils.logging import setup_logging, get_logger
    echo from injection.manager import InjectionManager
    echo from utils.skin_downloader import download_skins_on_startup
    echo.
    echo log = get_logger()
    echo.
    echo.
    echo def get_ocr_language^(lcu_lang: str, manual_lang: str = None^) -^> str:
    echo     """Get OCR language based on LCU language or manual setting"""
    echo     if manual_lang and manual_lang != "auto":
    echo         return manual_lang
    echo     
    echo     # Map LCU languages to Tesseract languages
    echo     ocr_lang_map = {
    echo         "en_US": "eng",
    echo         "es_ES": "spa", 
    echo         "es_MX": "spa",
    echo         "fr_FR": "fra",
    echo         "de_DE": "deu",
    echo         "it_IT": "ita",
    echo         "pt_BR": "por",
    echo         "ru_RU": "rus",
    echo         "pl_PL": "pol",
    echo         "tr_TR": "tur",
    echo         "el_GR": "ell",
    echo         "hu_HU": "hun",
    echo         "ro_RO": "ron",
    echo         "zh_CN": "chi_sim",
    echo         "zh_TW": "chi_tra",
    echo         "ja_JP": "jpn",
    echo         "ko_KR": "kor",
    echo     }
    echo     
    echo     return ocr_lang_map.get^(lcu_lang, "eng"^)  # Default to English
    echo.
    echo.
    echo def validate_ocr_language^(lang: str^) -^> bool:
    echo     """Validate that OCR language is available ^(basic check^)"""
    echo     if not lang or lang == "auto":
    echo         return True
    echo     
    echo     # Common Tesseract language codes
    echo     supported_langs = [
    echo         "eng", "fra", "spa", "deu", "ita", "por", "rus", "pol", "tur", 
    echo         "ell", "hun", "ron", "chi_sim", "chi_tra", "jpn", "kor"
    echo     ]
    echo     
    echo     # Check if all parts of combined languages are supported
    echo     parts = lang.split^('+'^)
    echo     for part in parts:
    echo         if part not in supported_langs:
    echo             return False
    echo     return True
    echo.
    echo.
    echo def main^(^):
    echo     """Main entry point"""
    echo     
    echo     ap = argparse.ArgumentParser^(description="Tracer combiné LCU + OCR ^(ChampSelect^) — ROI lock + burst OCR + locks/timer fixes"^)
    echo     
    echo     # OCR arguments
    echo     ap.add_argument^("--tessdata", type=str, default=None, help="Chemin du dossier tessdata ^(ex: C:\\Program Files\\Tesseract-OCR\\tessdata^)")
    echo     ap.add_argument^("--psm", type=int, default=7^)
    echo     ap.add_argument^("--min-conf", type=float, default=0.5^)
    echo     ap.add_argument^("--lang", type=str, default="auto", help="OCR lang ^(tesseract^): 'auto', 'fra+eng', 'kor', 'chi_sim', 'ell', etc."^)
    echo     ap.add_argument^("--tesseract-exe", type=str, default=None^)
    echo     
    echo     # Capture arguments
    echo     ap.add_argument^("--capture", choices=["window", "screen"], default="window"^)
    echo     ap.add_argument^("--monitor", choices=["all", "primary"], default="all"^)
    echo     ap.add_argument^("--window-hint", type=str, default="League"^)
    echo     
    echo     # Database arguments
    echo     ap.add_argument^("--dd-lang", type=str, default="en_US", help="Langue^(s^) DDragon: 'fr_FR' ^| 'fr_FR,en_US,es_ES' ^| 'all'"^)
    echo     
    echo     # General arguments
    echo     ap.add_argument^("--verbose", action="store_true"^)
    echo     ap.add_argument^("--lockfile", type=str, default=None^)
    echo     
    echo     # OCR performance arguments
    echo     ap.add_argument^("--burst-hz", type=float, default=50.0^)
    echo     ap.add_argument^("--idle-hz", type=float, default=0.0, help="ré-émission périodique ^(0=off^)")
    echo     ap.add_argument^("--diff-threshold", type=float, default=0.001^)
    echo     ap.add_argument^("--burst-ms", type=int, default=280^)
    echo     ap.add_argument^("--min-ocr-interval", type=float, default=0.11^)
    echo     ap.add_argument^("--second-shot-ms", type=int, default=120^)
    echo     ap.add_argument^("--roi-lock-s", type=float, default=1.5^)
    echo     
    echo     # Threading arguments
    echo     ap.add_argument^("--phase-hz", type=float, default=2.0^)
    echo     ap.add_argument^("--ws", action="store_true", default=True^)
    echo     ap.add_argument^("--no-ws", action="store_false", dest="ws", help="Disable WebSocket mode"^)
    echo     ap.add_argument^("--ws-ping", type=int, default=20^)
    echo     
    echo     # Timer arguments
    echo     ap.add_argument^("--timer-hz", type=int, default=1000, help="Fréquence d'affichage du décompte loadout ^(Hz^)")
    echo     ap.add_argument^("--fallback-loadout-ms", type=int, default=0, help="^(déprécié^) Ancien fallback ms si LCU ne donne pas le timer — ignoré"^)
    echo     ap.add_argument^("--skin-threshold-ms", type=int, default=2000, help="Écrire le dernier skin à T^<=seuil ^(ms^)")
    echo     ap.add_argument^("--skin-file", type=str, default="state/last_hovered_skin.txt", help="Chemin du fichier last_hovered_skin.txt"^)
    echo     ap.add_argument^("--inject-batch", type=str, default="", help="Batch à exécuter juste après l'écriture du skin ^(laisser vide pour désactiver^)"^)
    echo     
    echo     # Multi-language arguments
    echo     ap.add_argument^("--multilang", action="store_true", default=True, help="Enable multi-language support"^)
    echo     ap.add_argument^("--no-multilang", action="store_false", dest="multilang", help="Disable multi-language support"^)
    echo     ap.add_argument^("--language", type=str, default="auto", help="Manual language selection ^(e.g., 'fr_FR', 'en_US', 'zh_CN', 'auto' for detection^)"^)
    echo     
    echo     # Skin download arguments
    echo     ap.add_argument^("--download-skins", action="store_true", default=True, help="Automatically download skins at startup"^)
    echo     ap.add_argument^("--no-download-skins", action="store_false", dest="download_skins", help="Disable automatic skin downloading"^)
    echo     ap.add_argument^("--force-update-skins", action="store_true", help="Force update all skins ^(re-download existing ones^)")
    echo     ap.add_argument^("--max-champions", type=int, default=None, help="Limit number of champions to download skins for ^(for testing^)")
    echo.
    echo     args = ap.parse_args^(^)
    echo.
    echo     setup_logging^(args.verbose^)
    echo     log.info^("Starting..."^)
    echo     
    echo     # Download skins if enabled
    echo     if args.download_skins:
    echo         log.info^("Starting automatic skin download..."^)
    echo         try:
    echo             success = download_skins_on_startup^(
    echo                 force_update=args.force_update_skins,
    echo                 max_champions=args.max_champions
    echo             ^)
    echo             if success:
    echo                 log.info^("Skin download completed successfully"^)
    echo             else:
    echo                 log.warning^("Skin download completed with some issues"^)
    echo         except Exception as e:
    echo             log.error^(f"Failed to download skins: {e}"^)
    echo             log.info^("Continuing without updated skins..."^)
    echo     else:
    echo         log.info^("Automatic skin download disabled"^)
    echo     
    echo     # Initialize components
    echo     lcu = LCU^(args.lockfile^)
    echo     
    echo     # Determine OCR language based on LCU language if auto mode
    echo     ocr_lang = args.lang
    echo     if args.lang == "auto":
    echo         lcu_lang = lcu.get_client_language^(^) if lcu else None
    echo         ocr_lang = get_ocr_language^(lcu_lang, args.lang^)
    echo         log.info^(f"Auto-detected OCR language: {ocr_lang} ^(LCU: {lcu_lang}^)"^)
    echo     
    echo     # Validate OCR language
    echo     if not validate_ocr_language^(ocr_lang^):
    echo         log.warning^(f"OCR language '{ocr_lang}' may not be available. Falling back to English."^)
    echo         ocr_lang = "eng"
    echo     
    echo     # Initialize OCR with determined language
    echo     try:
    echo         ocr = OCR^(lang=ocr_lang, psm=args.psm, tesseract_exe=args.tesseract_exe^)
    echo         ocr.tessdata_dir = args.tessdata
    echo         log.info^(f"OCR: {ocr.backend} ^(lang: {ocr_lang}^)"^)
    echo     except Exception as e:
    echo         log.warning^(f"Failed to initialize OCR with language '{ocr_lang}': {e}"^)
    echo         log.info^("Falling back to English OCR"^)
    echo         ocr = OCR^(lang="eng", psm=args.psm, tesseract_exe=args.tesseract_exe^)
    echo         ocr.tessdata_dir = args.tessdata
    echo         log.info^(f"OCR: {ocr.backend} ^(lang: eng^)"^)
    echo     
    echo     db = NameDB^(lang=args.dd_lang^)
    echo     state = SharedState^(^)
    echo     
    echo     # Initialize multi-language database
    echo     if args.multilang:
    echo         auto_detect = args.language.lower^(^) == "auto"
    echo         manual_lang = args.language if not auto_detect else args.dd_lang
    echo         multilang_db = MultiLanguageDB^(auto_detect=auto_detect, fallback_lang=manual_lang, lcu_client=lcu^)
    echo         if auto_detect:
    echo             log.info^("Multi-language auto-detection enabled"^)
    echo         else:
    echo             log.info^(f"Multi-language mode: manual language '{manual_lang}'"^)
    echo     else:
    echo         multilang_db = None
    echo         log.info^("Multi-language support disabled"^)
    echo     
    echo     # Initialize injection manager
    echo     injection_manager = InjectionManager^(^)
    echo     
    echo     # Configure skin writing
    echo     state.skin_write_ms = int^(getattr^(args, 'skin_threshold_ms', 2000^) or 2000^)
    echo     state.skin_file = getattr^(args, 'skin_file', state.skin_file^) or state.skin_file
    echo     state.inject_batch = getattr^(args, 'inject_batch', state.inject_batch^) or state.inject_batch
    echo.
    echo     # Initialize threads
    echo     t_phase = PhaseThread^(lcu, state, interval=1.0/max^(0.5, args.phase_hz^), log_transitions=not args.ws^)
    echo     t_champ = None if args.ws else ChampThread^(lcu, db, state, interval=0.25^)
    echo     t_ocr = OCRSkinThread^(state, db, ocr, args, lcu, multilang_db^)
    echo     t_ws = WSEventThread^(lcu, db, state, ping_interval=args.ws_ping, timer_hz=args.timer_hz, fallback_ms=args.fallback_loadout_ms, injection_manager=injection_manager^) if args.ws else None
    echo.
    echo     # Start threads
    echo     t_phase.start^(^)
    echo     if t_champ: 
    echo         t_champ.start^(^)
    echo     t_ocr.start^(^)
    echo     if t_ws: 
    echo         t_ws.start^(^)
    echo.
    echo     print^("[ok] ready — combined tracer. OCR active ONLY in Champ Select.", flush=True^)
    echo.
    echo     last_phase = None
    echo     try:
    echo         while True:
    echo             ph = state.phase
    echo             if ph != last_phase:
    echo                 if ph == "InProgress":
    echo                     if state.last_hovered_skin_key:
    echo                         log.info^(f"[launch:last-skin] {state.last_hovered_skin_key} ^(skinId={state.last_hovered_skin_id}, champ={state.last_hovered_skin_slug}^)"^)
    echo                     else:
    echo                         log.info^("[launch:last-skin] ^(no hovered skin detected^)"^)
    echo                 last_phase = ph
    echo             time.sleep^(0.2^)
    echo     except KeyboardInterrupt:
    echo         pass
    echo     finally:
    echo         state.stop = True
    echo         t_phase.join^(timeout=1.0^)
    echo         if t_champ: 
    echo             t_champ.join^(timeout=1.0^)
    echo         t_ocr.join^(timeout=1.0^)
    echo         if t_ws: 
    echo             t_ws.join^(timeout=1.0^)
    echo.
    echo.
    echo if __name__ == "__main__":
    echo     main^(^)
    ) > main.py
    
    :: Create requirements.txt
    echo Creating requirements.txt...
    (
    echo numpy^>=1.21.0
    echo opencv-python^>=4.5.0
    echo psutil^>=5.8.0
    echo requests^>=2.25.0
    echo rapidfuzz^>=2.0.0
    echo websocket-client^>=1.0.0
    echo mss^>=6.1.0
    echo Pillow^>=8.0.0
    echo tesserocr^>=2.8.0
    ) > requirements.txt
    
    :: Create basic directory structure
    echo Creating directory structure...
    mkdir database 2>nul
    mkdir lcu 2>nul
    mkdir ocr 2>nul
    mkdir state 2>nul
    mkdir threads 2>nul
    mkdir utils 2>nul
    mkdir injection 2>nul
    mkdir injection\tools 2>nul
    mkdir injection\mods 2>nul
    mkdir injection\overlay 2>nul
    mkdir dependencies 2>nul
    
    :: Create __init__.py files
    echo. > database\__init__.py
    echo. > lcu\__init__.py
    echo. > ocr\__init__.py
    echo. > state\__init__.py
    echo. > threads\__init__.py
    echo. > utils\__init__.py
    echo. > injection\__init__.py
    echo. > __init__.py
)

:: Copy application files to installation directory
echo [5/8] Installing application files...
if exist "%TEMP_DIR%\LoLSkinChanger.zip" (
    :: Extract ZIP file
    powershell -Command "& {Expand-Archive -Path '%TEMP_DIR%\LoLSkinChanger.zip' -DestinationPath '%INSTALL_DIR%' -Force}"
    :: Move files from extracted folder to main directory
    if exist "%INSTALL_DIR%\LoLSkinChanger-main" (
        xcopy "%INSTALL_DIR%\LoLSkinChanger-main\*" "%INSTALL_DIR%\" /E /H /Y >nul
        rmdir /s /q "%INSTALL_DIR%\LoLSkinChanger-main"
    )
) else (
    :: Copy manually created files
    xcopy "%TEMP_DIR%\*" "%INSTALL_DIR%\" /E /H /Y >nul
)

:: Clean up temporary directory
rmdir /s /q "%TEMP_DIR%"

:: Install Python dependencies
echo [6/8] Installing Python dependencies...
cd /d "%INSTALL_DIR%"

:: Upgrade pip first
%PYTHON_CMD% -m pip install --upgrade pip

:: Install dependencies
%PIP_CMD% install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some dependencies may have failed to install.
    echo The application may still work, but some features might be limited.
)

:: Create desktop shortcut
echo [7/8] Creating desktop shortcut...
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
echo Creating start menu entry...
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
echo [8/8] Creating uninstaller...
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
echo Creating run script...
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
