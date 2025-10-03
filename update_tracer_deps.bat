@echo on
setlocal
cd /d "%~dp0"
call ".venv311\Scripts\activate.bat" || (echo ERROR: venv not found. Run setup_tracer.bat first. & pause & exit /b 1)
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -U numpy opencv-python Pillow mss psutil requests urllib3 websocket-client rapidfuzz

set "INSTALLED_OK=0"
for %%F in ("tesserocr-*.whl") do (
  if exist "%%~fF" (
    python -m pip install "%%~fF" && set INSTALLED_OK=1
    goto END
  )
)
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
  python -m pip install -U tesserocr==2.8.0 && set INSTALLED_OK=1
) else (
  echo ERROR: tesseract.exe not found. Please install it first.
)

:END
if not "%INSTALLED_OK%"=="1" echo ERROR: tesserocr update failed.
echo done> ".venv311\.setup_done"
echo UPDATE: Dependencies updated.
pause
