# LoL Skin Changer - Windows Installer

This package contains a complete Windows installer for the LoL Skin Changer application. The installer will automatically download and install everything required with zero user interaction.

## What the Installer Does

The installer automatically:

1. **Downloads and installs Python 3.11** (if not already installed)
2. **Downloads and installs Tesseract OCR** (if not already installed)
3. **Creates the LoL Skin Changer application structure**
4. **Installs all Python dependencies**
5. **Creates desktop and start menu shortcuts**
6. **Sets up environment variables**
7. **Creates an uninstaller**

## Installation Files

### Primary Installer (Recommended)
- **`install.bat`** - Main installer launcher (use this!)
- **`installer.ps1`** - PowerShell-based installer with full features

### Alternative Installer
- **`installer_simple.bat`** - Simple batch-based installer (fallback option)

## How to Use

### Option 1: Easy Installation (Recommended)
1. **Download the installer files**
2. **Double-click `install.bat`**
3. **Wait for installation to complete**
4. **Done!** The application will be ready to use

### Option 2: Alternative Installation
If the main installer fails:
1. **Double-click `installer_simple.bat`**
2. **Wait for installation to complete**

## What Gets Installed

### System Requirements
- **Python 3.11** - Downloaded and installed automatically
- **Tesseract OCR** - Downloaded and installed automatically
- **All Python dependencies** - Installed automatically

### Application Files
The installer creates a complete LoL Skin Changer application with:
- Main application (`main.py`)
- All required modules and dependencies
- Configuration files
- Database files
- Injection tools

### Installation Location
- **Default**: `%LOCALAPPDATA%\LoLSkinChanger`
- **Desktop Shortcut**: Created automatically
- **Start Menu Entry**: Created automatically

## Features

### Zero User Interaction
- No prompts or questions
- Automatic dependency resolution
- Silent installation of system components
- Automatic configuration

### Smart Detection
- Detects existing Python installation
- Detects existing Tesseract OCR installation
- Only downloads what's needed

### Complete Setup
- Creates all necessary directories
- Installs all dependencies
- Sets up environment variables
- Creates shortcuts and uninstaller

## Usage After Installation

### Starting the Application
1. **Desktop Shortcut** - Double-click the "LoL Skin Changer" shortcut
2. **Start Menu** - Find "LoL Skin Changer" in the Start Menu
3. **Command Line** - Run `python %LOCALAPPDATA%\LoLSkinChanger\main.py`

### How It Works
1. **Start League of Legends**
2. **Run the LoL Skin Changer**
3. **Enter Champion Select** - The system detects this automatically
4. **Hover over skins** - The system detects skin names using OCR
5. **Automatic injection** - Skins are injected before the game starts

## Uninstallation

To uninstall:
1. **Run the uninstaller**: `%LOCALAPPDATA%\LoLSkinChanger\uninstall.bat`
2. **Or manually delete**: The installation folder and shortcuts

**Note**: Python and Tesseract OCR are NOT removed by the uninstaller (they may be used by other applications).

## Troubleshooting

### Installation Fails
- **Check internet connection** - The installer downloads components
- **Run as administrator** - Right-click and "Run as administrator"
- **Try alternative installer** - Use `installer_simple.bat`

### Application Won't Start
- **Check Python installation** - Run `python --version` in command prompt
- **Check Tesseract installation** - Verify `%PROGRAMFILES%\Tesseract-OCR\tesseract.exe` exists
- **Check dependencies** - Run `pip install -r requirements.txt` in the installation folder

### OCR Not Working
- **Verify Tesseract** - Check that Tesseract OCR is properly installed
- **Check language packs** - Ensure required language packs are installed
- **Run with verbose logging** - Use `python main.py --verbose`

## System Requirements

### Minimum Requirements
- **Windows 10** or later
- **Internet connection** (for downloading components)
- **Administrator privileges** (for installing system components)
- **League of Legends** installed

### Recommended
- **Windows 11**
- **8GB RAM** or more
- **Fast internet connection**
- **League of Legends** with latest updates

## File Structure After Installation

```
%LOCALAPPDATA%\LoLSkinChanger\
├── main.py                 # Main application
├── requirements.txt        # Python dependencies
├── uninstall.bat          # Uninstaller
├── database\              # Champion/skin database
├── lcu\                   # League Client API
├── ocr\                   # OCR functionality
├── state\                 # Shared state
├── threads\               # Threading components
├── utils\                 # Utility functions
├── injection\             # Skin injection system
└── dependencies\          # Local dependencies
```

## Advanced Usage

### Command Line Options
The application supports many command-line options:

```bash
# Basic usage
python main.py

# Verbose logging
python main.py --verbose

# Specify language
python main.py --language fr_FR

# Disable automatic skin downloads
python main.py --no-download-skins

# Force update all skins
python main.py --force-update-skins
```

### Configuration
- **Language detection** - Automatic or manual
- **OCR settings** - Customizable for different languages
- **Performance tuning** - Adjustable for different systems
- **Skin management** - Automatic or manual skin downloads

## Support

### Common Issues
1. **"Python not found"** - The installer should handle this automatically
2. **"Tesseract not found"** - The installer should handle this automatically
3. **"Module not found"** - Run the installer again or check dependencies
4. **"Permission denied"** - Run as administrator

### Getting Help
- **Check the logs** - Use `--verbose` flag for detailed logging
- **Verify installation** - Check that all components are properly installed
- **Test dependencies** - Verify Python and Tesseract are working

## Security Notes

### What the Installer Downloads
- **Python 3.11** - Official Python installer from python.org
- **Tesseract OCR** - Official Tesseract installer from GitHub
- **Python packages** - From PyPI (Python Package Index)

### What the Installer Installs
- **System components** - Python and Tesseract OCR
- **Application files** - LoL Skin Changer application
- **Dependencies** - Python packages for the application
- **Shortcuts** - Desktop and start menu shortcuts

### No Malware
- **Open source** - All code is visible and auditable
- **Official sources** - Downloads from official repositories
- **No tracking** - No data collection or telemetry
- **Local installation** - Everything runs locally on your machine

## License

This installer is provided as-is for the LoL Skin Changer application. Please ensure you comply with all applicable terms of service and local laws when using this software.

---

**Ready to install? Just double-click `install.bat` and you're done!**
