@echo off
REM === run_tracer.bat ===
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

call ".venv311\Scripts\activate.bat"
set "TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\"

REM -- Dossiers / fichiers du skin injector (dossier frère de "OCR tracer")
set "SKIN_INJECTOR_DIR=%~dp0..\skin injector"
set "SKIN_FILE=%SKIN_INJECTOR_DIR%\last_hovered_skin.txt"
set "INJECT_BATCH=%SKIN_INJECTOR_DIR%\inject_skin.bat"

python -u "all_in_one_tracer.py" --ws --psm 7 ^
  --tessdata "C:\Program Files\Tesseract-OCR\tessdata" ^
  --burst-hz 2400 --burst-ms 800 --min-ocr-interval 0.04 --second-shot-ms 35 ^
  --diff-threshold 0.003 --idle-hz 0 --roi-lock-s 0.8 --min-conf 0.50 ^
  --phase-hz 6 ^
  --skin-threshold-ms 2000 ^
  --skin-file "%SKIN_FILE%" ^
  --inject-batch "%INJECT_BATCH%"

endlocal
