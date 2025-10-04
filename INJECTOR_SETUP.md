# Injector Setup Guide

This project requires an external skin injector to actually modify the game files. The application only handles detection and coordination.

## Required Components

### 1. Skin Injector
You need one of the following:
- **`cslol_tools_injector.py`** (recommended)
- **Custom batch file** (e.g., `inject_skin.bat`)
- **Other injection tool** that can read from `last_hovered_skin.txt`

### 2. Skin Files
- Place skin ZIP files in `incoming_zips/[ChampionName]/`
- Files should be named to match skin names detected by OCR
- See `incoming_zips/README.md` for directory structure

## How It Works

1. **Detection**: OCR detects skin names when you hover over them
2. **Coordination**: At 2-second threshold, writes skin name to `last_hovered_skin.txt`
3. **Injection**: External injector reads the file and injects the matching skin

## File Communication

The application communicates with the injector through:
- **Input**: `last_hovered_skin.txt` (contains detected skin name)
- **Output**: Injector processes the skin and modifies game files

## Setup Steps

1. **Get an injector**: Obtain `cslol_tools_injector.py` or create a batch file
2. **Add skins**: Place skin ZIP files in `incoming_zips/`
3. **Test**: Run the application and test skin detection
4. **Verify**: Check that injection occurs at 2-second threshold

## Troubleshooting

- **No injection**: Check that injector file exists and is executable
- **Wrong skin**: Verify skin ZIP files are named correctly
- **No match**: Check that skin names in ZIP files match OCR detection
