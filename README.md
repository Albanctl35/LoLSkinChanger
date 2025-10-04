# LoL Skin Changer - Fully Automated System

A complete League of Legends skin changer that automatically detects skins using OCR and injects them 2 seconds before the game starts. Just run `main.py` and it handles everything automatically - no manual intervention required!

## Project Structure

```
LoLSkinChanger/
├── main.py                     # Single automated launcher - RUN THIS!
├── requirements.txt            # Python dependencies
├── README.md                  # This file
├── injection/                 # Complete injection system
│   ├── __init__.py
│   ├── injector.py            # CSLOL injection logic
│   ├── manager.py             # Injection management
│   ├── mods_map.json          # Mod configuration
│   ├── tools/                 # CSLOL tools
│   │   ├── mod-tools.exe      # Main modification tool
│   │   ├── cslol-diag.exe     # Diagnostics tool
│   │   ├── cslol-dll.dll      # Core DLL
│   │   └── [other tools]      # WAD utilities
│   ├── incoming_zips/         # Skin collection (8,277+ skins)
│   │   └── skins/
│   │       ├── Aatrox/
│   │       ├── Ahri/
│   │       └── [171 champions]/
│   ├── mods/                  # Extracted skin mods
│   └── overlay/               # Temporary overlay files
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── normalization.py       # Text normalization utilities
│   ├── logging.py             # Logging configuration
│   ├── window_capture.py      # Windows window capture utilities
│   ├── skin_downloader.py     # Skin download system
│   ├── smart_skin_downloader.py # Smart downloader with rate limiting
│   └── repo_downloader.py     # Repository ZIP downloader
├── ocr/                       # OCR functionality
│   ├── __init__.py
│   ├── backend.py             # OCR backend implementation
│   └── image_processing.py    # Image processing for OCR
├── database/                  # Champion/skin database
│   ├── __init__.py
│   ├── name_db.py             # Champion and skin name database
│   └── multilang_db.py        # Multi-language database with auto-detection
├── lcu/                       # League Client API
│   ├── __init__.py
│   ├── client.py              # LCU API client
│   └── utils.py               # LCU utility functions
├── state/                     # Shared state
│   ├── __init__.py
│   ├── shared_state.py        # Shared state between threads
│   └── last_hovered_skin.txt  # Last hovered skin file
├── threads/                   # Threading components
│   ├── __init__.py
│   ├── phase_thread.py        # Game phase monitoring
│   ├── champ_thread.py        # Champion hover/lock monitoring
│   ├── ocr_thread.py          # OCR skin detection
│   ├── websocket_thread.py    # WebSocket event handling
│   └── loadout_ticker.py      # Loadout countdown timer
├── dependencies/              # Local dependencies
│   └── tesserocr-2.8.0-cp311-cp311-win_amd64.whl
└── [installer files]          # Windows installer components
```

## Features

- **Fully Automated**: Just run `main.py` - no manual intervention required!
- **Multi-Language Support**: Works with any League of Legends client language (17 languages supported)
- **⚠️ Limitation**: Languages with non-Latin alphabets (Chinese, Japanese, Korean, Arabic, etc.) are currently not supported due to OCR limitations
- **Smart Detection**: OCR automatically detects skin names during champion select
- **Instant Injection**: Skins are injected 2 seconds before game starts
- **Massive Collection**: 8,277+ skins for 171 champions included
- **Smart Downloads**: Efficient repository ZIP download with automatic updates
- **Fuzzy Matching**: Smart matching system for accurate skin detection
- **LCU Integration**: Real-time communication with League Client
- **CSLOL Tools**: Reliable injection using CSLOL modification tools
- **Modular Architecture**: Clean, maintainable codebase
- **Multi-threaded**: Optimal performance with concurrent processing
- **Optimized Loading**: Only loads necessary language databases for better performance

## Installation

1. Install Python 3.11 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   This will automatically install the local tesserocr wheel from the `dependencies/` folder.
3. Install Tesseract OCR on your system
4. Run the system:
   ```bash
   # That's it! Just run this:
   python main.py
   
   # Optional: Enable verbose logging
   python main.py --verbose
   
   # Optional: Enable WebSocket mode for better performance
   python main.py --ws
   
   # Optional: Specify language (auto-detection by default)
   python main.py --language es_ES    # Spanish
   python main.py --language fr_FR    # French
   python main.py --language zh_CN    # Chinese Simplified
   python main.py --language auto     # Auto-detect (default)
   
   # Optional: Specify OCR language for non-Latin alphabets
   python main.py --lang kor          # Korean OCR
   python main.py --lang chi_sim      # Chinese Simplified OCR
   python main.py --lang ell          # Greek OCR
   python main.py --lang auto         # Auto-detect OCR language (default)
   
   # Optional: Disable multi-language support
   python main.py --no-multilang
   
   # Optional: Control automatic skin downloading
   python main.py --no-download-skins        # Disable automatic skin downloads
   python main.py --force-update-skins       # Force update all skins
   python main.py --max-champions 10         # Limit to first 10 champions (for testing)
   ```

## Usage

### Fully Automated Mode (Default)
1. **Start the system**: `python main.py`
2. **That's it!** The system will:
   - Connect to League Client automatically
   - Monitor game phases (lobby, champion select, in-game)
   - Activate OCR when you enter champion select
   - Detect skin names as you hover over them
   - Automatically inject the skin after 2 seconds of hovering
   - Inject the skin 2 seconds before the game starts
   - Work completely automatically - no manual intervention!

### How It Works
1. **Launch League of Legends** and start a game
2. **Enter Champion Select** - the system detects this automatically
3. **Hover over skins** for 2+ seconds - the system detects the skin name
4. **The system automatically injects** the skin before the game starts
5. **Enjoy your custom skin** in the game!

### System Status
The system provides real-time status updates:
- **CHAMPION SELECT DETECTED** - OCR is active
- **GAME STARTING** - Last injected skin displayed
- **Detailed logs** with `--verbose` flag

## Command Line Arguments

### Core Options
- `--verbose`: Enable verbose logging
- `--ws`: Enable WebSocket mode for real-time events
- `--tessdata`: Specify Tesseract tessdata directory
- `--game-dir`: Specify League of Legends Game directory

### Skin Download Options
- `--download-skins`: Enable automatic skin downloading (default)
- `--no-download-skins`: Disable automatic skin downloading
- `--force-update-skins`: Force update all skins (re-download existing ones)
- `--max-champions <num>`: Limit number of champions to download skins for (for testing)

### Multi-Language Options
- `--multilang`: Enable multi-language support (default)
- `--no-multilang`: Disable multi-language support
- `--language <lang>`: Specify language or auto-detection
  - `auto`: Auto-detect language from LCU API (default)
  - `en_US`: English (United States)
  - `es_ES`: Spanish (Spain)
  - `fr_FR`: French
  - `de_DE`: German
  - `zh_CN`: Chinese (Simplified)
  - `ja_JP`: Japanese
  - `ko_KR`: Korean
  - `ru_RU`: Russian
  - `pt_BR`: Portuguese (Brazil)
  - `it_IT`: Italian
  - `tr_TR`: Turkish
  - `pl_PL`: Polish
  - `hu_HU`: Hungarian
  - `ro_RO`: Romanian
  - `el_GR`: Greek
  - `zh_TW`: Chinese (Traditional)
  - `es_MX`: Spanish (Mexico)

### OCR Language Options
- `--lang <ocr_lang>`: Specify OCR language for text recognition
  - `auto`: Auto-detect OCR language based on LCU language (default)
  - `eng`: English
  - `fra+eng`: French + English
  - `spa+eng`: Spanish + English
  - `deu+eng`: German + English
  - `kor+eng`: Korean + English
  - `chi_sim+eng`: Chinese Simplified + English
  - `chi_tra+eng`: Chinese Traditional + English
  - `jpn+eng`: Japanese + English
  - `ell+eng`: Greek + English
  - `rus+eng`: Russian + English
  - `pol+eng`: Polish + English
  - `tur+eng`: Turkish + English
  - `hun+eng`: Hungarian + English
  - `ron+eng`: Romanian + English
  - `por+eng`: Portuguese + English
  - `ita+eng`: Italian + English

### Supported Languages
The system supports 17 languages with automatic detection and optimized loading:
- **Auto-Detection**: Automatically detects language from LCU API and OCR text
- **Manual Selection**: Force specific language for better performance
- **Optimized Loading**: Only loads necessary language databases
- **OCR Language Mapping**: Automatically selects appropriate OCR language for non-Latin alphabets
- **English Mapping**: All results logged in English for consistency

## Dependencies

- numpy: Numerical operations
- opencv-python: Computer vision
- psutil: Process utilities
- requests: HTTP requests
- rapidfuzz: String matching
- tesserocr: OCR functionality
- websocket-client: WebSocket support
- mss: Screen capture
- Pillow: Image processing

## Troubleshooting

### Common Issues
- **No injection**: Check that CSLOL tools are present in `injection/tools/` directory
- **Wrong skin**: Verify skin names match the collection in `injection/incoming_zips/`
- **No match**: Check OCR detection accuracy with `--verbose` flag
- **Game not detected**: Ensure League of Legends is installed in default location
- **Language issues**: Use `--language auto` for automatic detection or specify your client's language
- **Performance issues**: Use manual language selection (`--language <lang>`) for better performance
- **Non-Latin alphabet issues**: Languages with non-Latin alphabets (Chinese, Japanese, Korean, Arabic, etc.) are currently not supported due to OCR limitations
- **OCR language not found**: Ensure Tesseract OCR has the required language packs installed

### System Requirements
- Python 3.11+
- Tesseract OCR installed
- League of Legends installed
- Windows operating system (for CSLOL tools)
- CSLOL tools present in `injection/tools/` directory

## Windows Installer

For easy installation on Windows, use the included installer:

1. **Download the installer package**
2. **Run `installer_complete.bat`**
3. **Wait for automatic installation**
4. **Done!** The application will be ready to use

The installer automatically:
- Downloads and installs Python 3.11
- Downloads and installs Tesseract OCR
- Installs the LoL Skin Changer application
- Creates desktop and start menu shortcuts
- Sets up all dependencies

See `INSTALLER_README.md` for detailed installer documentation.