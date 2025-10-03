# One-click setup & fast run — tesserocr only

Put these in `C:\Users\alban\Desktop\Skin changer\`:
  - all_in_one_tracer.py
  - setup_tracer.bat  (run once to create venv + install deps)
  - run_tracer_fast.bat  (daily use, starts immediately)
  - run_tracer.bat  (auto-setup variant if needed)
  - update_tracer_deps.bat  (optional updates later)
  - tesserocr-2.8.0-cp311-cp311-win_amd64.whl  (optional local wheel; recommended)

Requirements:
  - Tesseract OCR installed (default: `C:\Program Files\Tesseract-OCR\`)
  - Python 3.11 x64

First run:
  1) Double-click `setup_tracer.bat`.
  2) It creates `.venv311`, installs core deps, then installs `tesserocr` from local wheel if present, else via pip (requires Tesseract installed).

Daily:
  - Double-click `run_tracer_fast.bat` → immediate start (no pip).

Notes:
  - This build is **tesserocr-only**. If Tesseract or tesserocr is missing, setup stops with an error.
  - If your Tesseract is not in the default path, edit these in the `.bat` files:
    - `TESSDATA_PREFIX=...Tesseract-OCR\`
    - `--tessdata "...Tesseract-OCR\tessdata"`
