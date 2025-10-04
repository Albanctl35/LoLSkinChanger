# LoL Skin Changer - Modular Version

A modularized version of the League of Legends skin injector that detects skins using OCR and automatically injects them during champion select.

## Project Structure

```
LoLSkinChanger/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── dependencies/           # Local dependency files
│   ├── README.md          # Dependencies documentation
│   └── tesserocr-2.8.0-cp311-cp311-win_amd64.whl  # Tesseract OCR wheel
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── normalization.py   # Text normalization utilities
│   ├── logging.py         # Logging configuration
│   └── window_capture.py  # Windows window capture utilities
├── ocr/                   # OCR functionality
│   ├── __init__.py
│   ├── backend.py         # OCR backend implementation
│   └── image_processing.py # Image processing for OCR
├── database/              # Data Dragon database
│   ├── __init__.py
│   └── name_db.py         # Champion and skin name database
├── lcu/                   # League Client API
│   ├── __init__.py
│   ├── client.py          # LCU API client
│   └── utils.py           # LCU utility functions
├── state/                 # Shared state
│   ├── __init__.py
│   └── shared_state.py    # Shared state between threads
└── threads/               # Threading components
    ├── __init__.py
    ├── phase_thread.py    # Game phase monitoring
    ├── champ_thread.py    # Champion hover/lock monitoring
    ├── ocr_thread.py      # OCR skin detection
    ├── websocket_thread.py # WebSocket event handling
    └── loadout_ticker.py  # Loadout countdown timer
```

## Features

- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **OCR Skin Detection**: Uses Tesseract OCR to detect skin names from the game UI
- **Automatic Injection**: Automatically injects the last detected skin when champion select ends
- **LCU Integration**: Communicates with the League Client API for game state
- **WebSocket Support**: Real-time event handling via WebSocket connection
- **Multi-threaded**: Concurrent processing for optimal performance

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   This will automatically install the local tesserocr wheel from the `dependencies/` folder.
3. Install Tesseract OCR on your system
4. Run the application:
   ```bash
   python main.py
   ```

## Usage

The application runs automatically once started. It will:
1. Monitor the game phase
2. Detect when you're in champion select
3. Use OCR to detect skin names as you hover over them
4. Automatically inject the last detected skin when the countdown reaches 2 seconds

## Command Line Arguments

- `--verbose`: Enable verbose logging
- `--ws`: Enable WebSocket mode for real-time events
- `--timer-hz`: Set countdown display frequency (default: 1000 Hz)
- `--skin-threshold-ms`: Set skin write threshold in milliseconds (default: 2000)
- `--skin-file`: Path to the skin file to write
- `--inject-batch`: Path to the injection batch file

## Original vs Modular

This modular version maintains 100% of the original functionality while providing:
- Better code organization
- Easier maintenance
- Clear separation of concerns
- Improved readability
- Better error handling

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