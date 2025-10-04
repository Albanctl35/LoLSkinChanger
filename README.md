# LoL Skin Changer - Fully Automated System

A complete League of Legends skin changer that automatically detects skins using OCR and injects them 2 seconds before the game starts. Just run `main.py` and it handles everything automatically - no manual intervention required!

## Project Structure

```
OCR tracer/
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
│   ├── incoming_zips/         # Skin collection (8,000+ skins)
│   │   ├── Aatrox/
│   │   ├── Ahri/
│   │   └── [150+ champions]/
│   ├── mods/                  # Extracted skin mods
│   └── overlay/               # Temporary overlay files
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── normalization.py       # Text normalization utilities
│   ├── logging.py             # Logging configuration
│   └── window_capture.py      # Windows window capture utilities
├── ocr/                       # OCR functionality
│   ├── __init__.py
│   ├── backend.py             # OCR backend implementation
│   └── image_processing.py    # Image processing for OCR
├── database/                  # Champion/skin database
│   ├── __init__.py
│   └── name_db.py             # Champion and skin name database
├── lcu/                       # League Client API
│   ├── __init__.py
│   ├── client.py              # LCU API client
│   └── utils.py               # LCU utility functions
├── state/                     # Shared state
│   ├── __init__.py
│   └── shared_state.py        # Shared state between threads
└── threads/                   # Threading components
    ├── __init__.py
    ├── phase_thread.py        # Game phase monitoring
    ├── champ_thread.py        # Champion hover/lock monitoring
    ├── ocr_thread.py          # OCR skin detection
    ├── websocket_thread.py    # WebSocket event handling
    └── loadout_ticker.py      # Loadout countdown timer
```

## Features

- **Fully Automated**: Just run `main.py` - no manual intervention required!
- **Smart Detection**: OCR automatically detects skin names during champion select
- **Instant Injection**: Skins are injected 2 seconds before game starts
- **Massive Collection**: 8,000+ skins for 150+ champions included
- **Fuzzy Matching**: Smart matching system for accurate skin detection
- **LCU Integration**: Real-time communication with League Client
- **CSLOL Tools**: Reliable injection using CSLOL modification tools
- **Modular Architecture**: Clean, maintainable codebase
- **Multi-threaded**: Optimal performance with concurrent processing

## Installation

1. Install Python 3.8 or higher
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

- `--verbose`: Enable verbose logging
- `--ws`: Enable WebSocket mode for real-time events
- `--tessdata`: Specify Tesseract tessdata directory
- `--game-dir`: Specify League of Legends Game directory

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

### System Requirements
- Python 3.8+
- Tesseract OCR installed
- League of Legends installed
- Windows operating system (for CSLOL tools)
- CSLOL tools present in `injection/tools/` directory