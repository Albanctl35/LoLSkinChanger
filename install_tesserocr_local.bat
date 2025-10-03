@echo on
setlocal
cd /d "%~dp0"
if not exist ".venv311\Scripts\python.exe" (
  echo ERROR: No venv found. Run setup_tracer.bat first.
  pause
  exit /b 1
)
call ".venv311\Scripts\activate.bat"
for %%F in ("tesserocr-*.whl") do (
  if exist "%%~fF" (
    echo Installing %%~nxF ...
    python -m pip install "%%~fF"
    goto END
  )
)
echo ERROR: No tesserocr-*.whl found in this folder.
:END
pause
