@echo off
REM ============================================================================
REM  MarketingOps Agent - ONE-CLICK LAUNCHER (Windows)
REM  Double-click this file (or the Desktop shortcut). It sets up everything,
REM  auto-installs Python if needed, and opens the web UI in your browser.
REM ============================================================================
setlocal
cd /d "%~dp0"

REM free port 8000 if an old server is still running
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [1/4] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
  echo       Python not found - installing once (needs internet)...
  powershell -NoProfile -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile \"$env:TEMP\py_install.exe\""
  if not exist "%TEMP%\py_install.exe" (
    echo [!] Could not download Python. Connect to the internet and retry.
    pause
    exit /b 1
  )
  start /wait "" "%TEMP%\py_install.exe" /quiet PrependPath=1 IncludePip=1
  del "%TEMP%\py_install.exe" >nul 2>&1
  REM refresh PATH for this session
  for /f "tokens=*" %%p in ('powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%p;%PATH%"
)
where python >nul 2>&1 || (
  echo [!] Python still not found. Restart your PC and try again (or install from python.org).
  pause
  exit /b 1
)

echo [2/4] Setting up environment (one time)...
if not exist ".venv" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if not exist ".env" copy .env.example .env >nul

echo [3/4] Creating Desktop shortcut (so you never open this folder again)...
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $p=[Environment]::GetFolderPath('Desktop')+'\MarketingOps Agent.lnk'; $s=$ws.CreateShortcut($p); $s.TargetPath='%~f0'; $s.WorkingDirectory='%CD%'; $s.Description='MarketingOps Agent - marketing assistant'; $s.Save()"

echo [4/4] Starting the agent and opening your browser...
start "MarketingOps Agent" /min .venv\Scripts\python cli.py web
powershell -NoProfile -Command "$n=0; while($n -lt 40){ try { if((Invoke-WebRequest http://localhost:8000/api/status -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200){ break } } catch {} ; Start-Sleep -Seconds 1; $n++ }; Start-Process http://localhost:8000"

echo.
echo    All done. The agent is open at:  http://localhost:8000
echo    From now on, just double-click the "MarketingOps Agent" icon on your Desktop.
echo    To stop it: close the "MarketingOps Agent" window, or double-click stop.bat.
echo.
exit /b 0
