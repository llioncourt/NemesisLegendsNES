@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "tools\rebuild_evidence.py" %*
) else (
  py -3 "tools\rebuild_evidence.py" %*
)
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo Rebuild failed. Check the message above; this is not a game-ROM builder.
exit /b %RESULT%
