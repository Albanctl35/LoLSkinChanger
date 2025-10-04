# LoL Skin Changer - Complete Windows Installer
# PowerShell-based installer that can be compiled into an executable

param(
    [switch]$Silent = $false,
    [string]$InstallPath = "$env:LOCALAPPDATA\LoLSkinChanger"
)

# Set execution policy for this script
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Function to write colored output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to download file with progress
function Download-FileWithProgress {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Description
    )
    
    try {
        Write-ColorOutput Yellow "Downloading $Description..."
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $OutputPath)
        return $true
    }
    catch {
        Write-ColorOutput Red "Failed to download $Description`: $($_.Exception.Message)"
        return $false
    }
}

# Function to install Python
function Install-Python {
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-ColorOutput Green "Python is already installed."
        return $true
    }
    
    if (-not (Download-FileWithProgress -Url $pythonUrl -OutputPath $pythonInstaller -Description "Python 3.11")) {
        return $false
    }
    
    Write-ColorOutput Yellow "Installing Python 3.11..."
    $process = Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait -PassThru
    
    Start-Sleep -Seconds 10
    Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
    
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-ColorOutput Green "Python installed successfully."
        return $true
    } else {
        Write-ColorOutput Red "Python installation failed."
        return $false
    }
}

# Function to install Tesseract OCR
function Install-Tesseract {
    $tesseractUrl = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    $tesseractInstaller = "$env:TEMP\tesseract-installer.exe"
    $tesseractPath = "${env:ProgramFiles}\Tesseract-OCR"
    
    if (Test-Path "$tesseractPath\tesseract.exe") {
        Write-ColorOutput Green "Tesseract OCR is already installed."
        return $true
    }
    
    if (-not (Download-FileWithProgress -Url $tesseractUrl -OutputPath $tesseractInstaller -Description "Tesseract OCR")) {
        return $false
    }
    
    Write-ColorOutput Yellow "Installing Tesseract OCR..."
    $process = Start-Process -FilePath $tesseractInstaller -ArgumentList "/S", "/D=$tesseractPath" -Wait -PassThru
    
    Start-Sleep -Seconds 10
    Remove-Item $tesseractInstaller -Force -ErrorAction SilentlyContinue
    
    if (Test-Path "$tesseractPath\tesseract.exe") {
        Write-ColorOutput Green "Tesseract OCR installed successfully."
        return $true
    } else {
        Write-ColorOutput Red "Tesseract OCR installation failed."
        return $false
    }
}

# Function to create application structure
function New-ApplicationStructure {
    param([string]$Path)
    
    $directories = @(
        "database",
        "lcu", 
        "ocr",
        "state",
        "threads",
        "utils",
        "injection",
        "injection\tools",
        "injection\mods",
        "injection\overlay",
        "dependencies"
    )
    
    foreach ($dir in $directories) {
        $fullPath = Join-Path $Path $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }
    
    # Create __init__.py files
    $initFiles = @(
        "database\__init__.py",
        "lcu\__init__.py",
        "ocr\__init__.py", 
        "state\__init__.py",
        "threads\__init__.py",
        "utils\__init__.py",
        "injection\__init__.py",
        "__init__.py"
    )
    
    foreach ($file in $initFiles) {
        $fullPath = Join-Path $Path $file
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType File -Path $fullPath -Force | Out-Null
        }
    }
}

# Function to create main.py
function New-MainPy {
    param([string]$Path)
    
    $mainPyContent = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the modularized LoL Skin Changer
"""

import argparse
import time
from ocr.backend import OCR
from database.name_db import NameDB
from database.multilang_db import MultiLanguageDB
from lcu.client import LCU
from state.shared_state import SharedState
from threads.phase_thread import PhaseThread
from threads.champ_thread import ChampThread
from threads.ocr_thread import OCRSkinThread
from threads.websocket_thread import WSEventThread
from utils.logging import setup_logging, get_logger
from injection.manager import InjectionManager
from utils.skin_downloader import download_skins_on_startup

log = get_logger()


def get_ocr_language(lcu_lang: str, manual_lang: str = None) -> str:
    """Get OCR language based on LCU language or manual setting"""
    if manual_lang and manual_lang != "auto":
        return manual_lang
    
    # Map LCU languages to Tesseract languages
    ocr_lang_map = {
        "en_US": "eng",
        "es_ES": "spa", 
        "es_MX": "spa",
        "fr_FR": "fra",
        "de_DE": "deu",
        "it_IT": "ita",
        "pt_BR": "por",
        "ru_RU": "rus",
        "pl_PL": "pol",
        "tr_TR": "tur",
        "el_GR": "ell",
        "hu_HU": "hun",
        "ro_RO": "ron",
        "zh_CN": "chi_sim",
        "zh_TW": "chi_tra",
        "ja_JP": "jpn",
        "ko_KR": "kor",
    }
    
    return ocr_lang_map.get(lcu_lang, "eng")  # Default to English


def validate_ocr_language(lang: str) -> bool:
    """Validate that OCR language is available (basic check)"""
    if not lang or lang == "auto":
        return True
    
    # Common Tesseract language codes
    supported_langs = [
        "eng", "fra", "spa", "deu", "ita", "por", "rus", "pol", "tur", 
        "ell", "hun", "ron", "chi_sim", "chi_tra", "jpn", "kor"
    ]
    
    # Check if all parts of combined languages are supported
    parts = lang.split('+')
    for part in parts:
        if part not in supported_langs:
            return False
    return True


def main():
    """Main entry point"""
    
    ap = argparse.ArgumentParser(description="Tracer combiné LCU + OCR (ChampSelect) — ROI lock + burst OCR + locks/timer fixes")
    
    # OCR arguments
    ap.add_argument("--tessdata", type=str, default=None, help="Chemin du dossier tessdata (ex: C:\\Program Files\\Tesseract-OCR\\tessdata)")
    ap.add_argument("--psm", type=int, default=7)
    ap.add_argument("--min-conf", type=float, default=0.5)
    ap.add_argument("--lang", type=str, default="auto", help="OCR lang (tesseract): 'auto', 'fra+eng', 'kor', 'chi_sim', 'ell', etc.")
    ap.add_argument("--tesseract-exe", type=str, default=None)
    
    # Capture arguments
    ap.add_argument("--capture", choices=["window", "screen"], default="window")
    ap.add_argument("--monitor", choices=["all", "primary"], default="all")
    ap.add_argument("--window-hint", type=str, default="League")
    
    # Database arguments
    ap.add_argument("--dd-lang", type=str, default="en_US", help="Langue(s) DDragon: 'fr_FR' | 'fr_FR,en_US,es_ES' | 'all'")
    
    # General arguments
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--lockfile", type=str, default=None)
    
    # OCR performance arguments
    ap.add_argument("--burst-hz", type=float, default=50.0)
    ap.add_argument("--idle-hz", type=float, default=0.0, help="ré-émission périodique (0=off)")
    ap.add_argument("--diff-threshold", type=float, default=0.001)
    ap.add_argument("--burst-ms", type=int, default=280)
    ap.add_argument("--min-ocr-interval", type=float, default=0.11)
    ap.add_argument("--second-shot-ms", type=int, default=120)
    ap.add_argument("--roi-lock-s", type=float, default=1.5)
    
    # Threading arguments
    ap.add_argument("--phase-hz", type=float, default=2.0)
    ap.add_argument("--ws", action="store_true", default=True)
    ap.add_argument("--no-ws", action="store_false", dest="ws", help="Disable WebSocket mode")
    ap.add_argument("--ws-ping", type=int, default=20)
    
    # Timer arguments
    ap.add_argument("--timer-hz", type=int, default=1000, help="Fréquence d'affichage du décompte loadout (Hz)")
    ap.add_argument("--fallback-loadout-ms", type=int, default=0, help="(déprécié) Ancien fallback ms si LCU ne donne pas le timer — ignoré")
    ap.add_argument("--skin-threshold-ms", type=int, default=2000, help="Écrire le dernier skin à T<=seuil (ms)")
    ap.add_argument("--skin-file", type=str, default="state/last_hovered_skin.txt", help="Chemin du fichier last_hovered_skin.txt")
    ap.add_argument("--inject-batch", type=str, default="", help="Batch à exécuter juste après l'écriture du skin (laisser vide pour désactiver)")
    
    # Multi-language arguments
    ap.add_argument("--multilang", action="store_true", default=True, help="Enable multi-language support")
    ap.add_argument("--no-multilang", action="store_false", dest="multilang", help="Disable multi-language support")
    ap.add_argument("--language", type=str, default="auto", help="Manual language selection (e.g., 'fr_FR', 'en_US', 'zh_CN', 'auto' for detection)")
    
    # Skin download arguments
    ap.add_argument("--download-skins", action="store_true", default=True, help="Automatically download skins at startup")
    ap.add_argument("--no-download-skins", action="store_false", dest="download_skins", help="Disable automatic skin downloading")
    ap.add_argument("--force-update-skins", action="store_true", help="Force update all skins (re-download existing ones)")
    ap.add_argument("--max-champions", type=int, default=None, help="Limit number of champions to download skins for (for testing)")

    args = ap.parse_args()

    setup_logging(args.verbose)
    log.info("Starting...")
    
    # Download skins if enabled
    if args.download_skins:
        log.info("Starting automatic skin download...")
        try:
            success = download_skins_on_startup(
                force_update=args.force_update_skins,
                max_champions=args.max_champions
            )
            if success:
                log.info("Skin download completed successfully")
            else:
                log.warning("Skin download completed with some issues")
        except Exception as e:
            log.error(f"Failed to download skins: {e}")
            log.info("Continuing without updated skins...")
    else:
        log.info("Automatic skin download disabled")
    
    # Initialize components
    lcu = LCU(args.lockfile)
    
    # Determine OCR language based on LCU language if auto mode
    ocr_lang = args.lang
    if args.lang == "auto":
        lcu_lang = lcu.get_client_language() if lcu else None
        ocr_lang = get_ocr_language(lcu_lang, args.lang)
        log.info(f"Auto-detected OCR language: {ocr_lang} (LCU: {lcu_lang})")
    
    # Validate OCR language
    if not validate_ocr_language(ocr_lang):
        log.warning(f"OCR language '{ocr_lang}' may not be available. Falling back to English.")
        ocr_lang = "eng"
    
    # Initialize OCR with determined language
    try:
        ocr = OCR(lang=ocr_lang, psm=args.psm, tesseract_exe=args.tesseract_exe)
        ocr.tessdata_dir = args.tessdata
        log.info(f"OCR: {ocr.backend} (lang: {ocr_lang})")
    except Exception as e:
        log.warning(f"Failed to initialize OCR with language '{ocr_lang}': {e}")
        log.info("Falling back to English OCR")
        ocr = OCR(lang="eng", psm=args.psm, tesseract_exe=args.tesseract_exe)
        ocr.tessdata_dir = args.tessdata
        log.info(f"OCR: {ocr.backend} (lang: eng)")
    
    db = NameDB(lang=args.dd_lang)
    state = SharedState()
    
    # Initialize multi-language database
    if args.multilang:
        auto_detect = args.language.lower() == "auto"
        manual_lang = args.language if not auto_detect else args.dd_lang
        multilang_db = MultiLanguageDB(auto_detect=auto_detect, fallback_lang=manual_lang, lcu_client=lcu)
        if auto_detect:
            log.info("Multi-language auto-detection enabled")
        else:
            log.info(f"Multi-language mode: manual language '{manual_lang}'")
    else:
        multilang_db = None
        log.info("Multi-language support disabled")
    
    # Initialize injection manager
    injection_manager = InjectionManager()
    
    # Configure skin writing
    state.skin_write_ms = int(getattr(args, 'skin_threshold_ms', 2000) or 2000)
    state.skin_file = getattr(args, 'skin_file', state.skin_file) or state.skin_file
    state.inject_batch = getattr(args, 'inject_batch', state.inject_batch) or state.inject_batch

    # Initialize threads
    t_phase = PhaseThread(lcu, state, interval=1.0/max(0.5, args.phase_hz), log_transitions=not args.ws)
    t_champ = None if args.ws else ChampThread(lcu, db, state, interval=0.25)
    t_ocr = OCRSkinThread(state, db, ocr, args, lcu, multilang_db)
    t_ws = WSEventThread(lcu, db, state, ping_interval=args.ws_ping, timer_hz=args.timer_hz, fallback_ms=args.fallback_loadout_ms, injection_manager=injection_manager) if args.ws else None

    # Start threads
    t_phase.start()
    if t_champ: 
        t_champ.start()
    t_ocr.start()
    if t_ws: 
        t_ws.start()

    print("[ok] ready — combined tracer. OCR active ONLY in Champ Select.", flush=True)

    last_phase = None
    try:
        while True:
            ph = state.phase
            if ph != last_phase:
                if ph == "InProgress":
                    if state.last_hovered_skin_key:
                        log.info(f"[launch:last-skin] {state.last_hovered_skin_key} (skinId={state.last_hovered_skin_id}, champ={state.last_hovered_skin_slug})")
                    else:
                        log.info("[launch:last-skin] (no hovered skin detected)")
                last_phase = ph
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        state.stop = True
        t_phase.join(timeout=1.0)
        if t_champ: 
            t_champ.join(timeout=1.0)
        t_ocr.join(timeout=1.0)
        if t_ws: 
            t_ws.join(timeout=1.0)


if __name__ == "__main__":
    main()
'@
    
    $mainPyPath = Join-Path $Path "main.py"
    Set-Content -Path $mainPyPath -Value $mainPyContent -Encoding UTF8
}

# Function to create requirements.txt
function New-RequirementsTxt {
    param([string]$Path)
    
    $requirementsContent = @'
numpy>=1.21.0
opencv-python>=4.5.0
psutil>=5.8.0
requests>=2.25.0
rapidfuzz>=2.0.0
websocket-client>=1.0.0
mss>=6.1.0
Pillow>=8.0.0
tesserocr>=2.8.0
'@
    
    $requirementsPath = Join-Path $Path "requirements.txt"
    Set-Content -Path $requirementsPath -Value $requirementsContent -Encoding UTF8
}

# Function to create shortcuts
function New-Shortcuts {
    param([string]$InstallPath)
    
    $WshShell = New-Object -comObject WScript.Shell
    
    # Desktop shortcut
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\LoL Skin Changer.lnk")
    $DesktopShortcut.TargetPath = "python"
    $DesktopShortcut.Arguments = "`"$InstallPath\main.py`""
    $DesktopShortcut.WorkingDirectory = $InstallPath
    $DesktopShortcut.Description = "LoL Skin Changer"
    $DesktopShortcut.Save()
    
    # Start Menu shortcut
    $StartMenuPath = [Environment]::GetFolderPath("StartMenu")
    $StartMenuDir = "$StartMenuPath\LoL Skin Changer"
    if (-not (Test-Path $StartMenuDir)) {
        New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
    }
    
    $StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuDir\LoL Skin Changer.lnk")
    $StartMenuShortcut.TargetPath = "python"
    $StartMenuShortcut.Arguments = "`"$InstallPath\main.py`""
    $StartMenuShortcut.WorkingDirectory = $InstallPath
    $StartMenuShortcut.Description = "LoL Skin Changer"
    $StartMenuShortcut.Save()
}

# Function to create uninstaller
function New-Uninstaller {
    param([string]$InstallPath)
    
    $uninstallerContent = @'
@echo off
echo Uninstalling LoL Skin Changer...
echo.
echo This will remove:
echo - LoL Skin Changer application files
echo - Desktop shortcut
echo - Start menu entry
echo.
echo Python and Tesseract OCR will NOT be removed.
echo.
pause
echo.
echo Removing application files...
if exist "{0}" rmdir /s /q "{0}"
echo.
echo Removing shortcuts...
if exist "{1}\LoL Skin Changer.lnk" del "{1}\LoL Skin Changer.lnk"
if exist "{2}\LoL Skin Changer" rmdir /s /q "{2}\LoL Skin Changer"
echo.
echo Uninstallation complete!
pause
'@ -f $InstallPath, [Environment]::GetFolderPath("Desktop"), [Environment]::GetFolderPath("StartMenu")
    
    $uninstallerPath = Join-Path $InstallPath "uninstall.bat"
    Set-Content -Path $uninstallerPath -Value $uninstallerContent -Encoding ASCII
}

# Main installation process
try {
    if (-not $Silent) {
        Write-ColorOutput Cyan "================================================"
        Write-ColorOutput Cyan "    LoL Skin Changer - Complete Installer"
        Write-ColorOutput Cyan "================================================"
        Write-ColorOutput White ""
        Write-ColorOutput White "This installer will automatically download and install:"
        Write-ColorOutput White "- Python 3.11 (if not already installed)"
        Write-ColorOutput White "- Tesseract OCR"
        Write-ColorOutput White "- LoL Skin Changer application"
        Write-ColorOutput White "- All required dependencies"
        Write-ColorOutput White ""
        Write-ColorOutput Yellow "Please wait while the installation proceeds..."
        Write-ColorOutput White ""
    }
    
    # Step 1: Create installation directory
    Write-ColorOutput Yellow "[1/6] Creating installation directory..."
    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    }
    
    # Step 2: Install Python
    Write-ColorOutput Yellow "[2/6] Installing Python..."
    if (-not (Install-Python)) {
        throw "Python installation failed"
    }
    
    # Step 3: Install Tesseract OCR
    Write-ColorOutput Yellow "[3/6] Installing Tesseract OCR..."
    if (-not (Install-Tesseract)) {
        throw "Tesseract OCR installation failed"
    }
    
    # Step 4: Create application structure
    Write-ColorOutput Yellow "[4/6] Creating application structure..."
    New-ApplicationStructure -Path $InstallPath
    New-MainPy -Path $InstallPath
    New-RequirementsTxt -Path $InstallPath
    
    # Step 5: Install Python dependencies
    Write-ColorOutput Yellow "[5/6] Installing Python dependencies..."
    Set-Location $InstallPath
    
    # Upgrade pip
    python -m pip install --upgrade pip | Out-Null
    
    # Install requirements
    $pipResult = python -m pip install -r requirements.txt 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Yellow "Warning: Some dependencies may have failed to install."
        Write-ColorOutput Yellow "The application may still work, but some features might be limited."
    }
    
    # Step 6: Create shortcuts and uninstaller
    Write-ColorOutput Yellow "[6/6] Creating shortcuts and uninstaller..."
    New-Shortcuts -InstallPath $InstallPath
    New-Uninstaller -InstallPath $InstallPath
    
    # Set environment variables
    [Environment]::SetEnvironmentVariable("TESSERACT_CMD", "${env:ProgramFiles}\Tesseract-OCR\tesseract.exe", "User")
    [Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", "${env:ProgramFiles}\Tesseract-OCR\tessdata", "User")
    
    # Installation complete
    if (-not $Silent) {
        Write-ColorOutput White ""
        Write-ColorOutput Green "================================================"
        Write-ColorOutput Green "    Installation Complete!"
        Write-ColorOutput Green "================================================"
        Write-ColorOutput White ""
        Write-ColorOutput Green "LoL Skin Changer has been successfully installed!"
        Write-ColorOutput White ""
        Write-ColorOutput White "Installation location: $InstallPath"
        Write-ColorOutput White ""
        Write-ColorOutput White "You can now:"
        Write-ColorOutput White "1. Double-click the desktop shortcut to start the application"
        Write-ColorOutput White "2. Or use the Start Menu entry"
        Write-ColorOutput White ""
        Write-ColorOutput White "To uninstall, run: $InstallPath\uninstall.bat"
        Write-ColorOutput White ""
        Write-ColorOutput White "The application will automatically:"
        Write-ColorOutput White "- Connect to League of Legends"
        Write-ColorOutput White "- Detect skins during champion select"
        Write-ColorOutput White "- Inject skins before the game starts"
        Write-ColorOutput White ""
        Write-ColorOutput Green "Enjoy your custom skins!"
        Write-ColorOutput White ""
    }
    
    Write-Output "Installation completed successfully."
}
catch {
    Write-ColorOutput Red "Installation failed: $($_.Exception.Message)"
    if (-not $Silent) {
        Write-ColorOutput White ""
        Write-ColorOutput Red "Please check the error messages above and try again."
        Write-ColorOutput White ""
        Read-Host "Press Enter to exit"
    }
    exit 1
}
