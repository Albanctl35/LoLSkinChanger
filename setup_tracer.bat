@echo on
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

set "PY_EXE="
for %%P in (py.exe) do if exist "%%~$PATH:P" set "PY_EXE=py"
if not defined PY_EXE for %%P in (python.exe) do if exist "%%~$PATH:P" set "PY_EXE=python"
if not defined PY_EXE (
  echo ERROR: Python not found. Please install Python 3.11+.
  pause
  exit /b 1
)

if not exist ".venv311\Scripts\python.exe" (
  echo SETUP: Creating virtual environment .venv311 ...
  %PY_EXE% -3.11 -m venv ".venv311" 2>nul || %PY_EXE% -3 -m venv ".venv311"
)

call ".venv311\Scripts\activate.bat" || (echo ERROR: venv activation failed. & pause & exit /b 1)

python -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
echo SETUP: Installing dependencies one time ...
python -m pip install -q numpy opencv-python Pillow mss psutil requests urllib3 websocket-client rapidfuzz

set "INSTALLED_OK=0"
for %%F in ("tesserocr-*.whl") do (
  if exist "%%~fF" (
    echo SETUP: Installing local %%~nxF ...
    python -m pip install "%%~fF" && set INSTALLED_OK=1
    goto MARK
  )
)

if not "%INSTALLED_OK%"=="1" (
  if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo SETUP: Installing tesserocr 2.8.0 from pip ...
    python -m pip install tesserocr==2.8.0 && set INSTALLED_OK=1
  ) else (
    echo ERROR: tesseract.exe not found at C:\Program Files\Tesseract-OCR\tesseract.exe
    pause
    exit /b 1
  )
)

:MARK
if not "%INSTALLED_OK%"=="1" (
  echo ERROR: Failed to install tesserocr. Aborting.
  pause
  exit /b 1
)

echo done> ".venv311\.setup_done"
echo OK: Initial setup complete.
pause
