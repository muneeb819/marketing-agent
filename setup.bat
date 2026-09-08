@echo off
REM ============================================================================
REM  MarketingOps Agent - ONE-TIME FULL SETUP (Windows)
REM  Double-click this. It installs Python (if needed), the agent, Ollama + model,
REM  creates a Desktop shortcut, and opens your public link. Then just use it.
REM ============================================================================
setlocal
cd /d "%~dp0"

REM free port 8000 if an old server is running
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [1/6] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
  echo       Python not found - installing once. Needs internet.
  powershell -NoProfile -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile \"$env:TEMP\py_install.exe\""
  if not exist "%TEMP%\py_install.exe" ( echo [!] Download failed. Connect to internet and retry. pause & exit /b 1 )
  start /wait "" "%TEMP%\py_install.exe" /quiet PrependPath=1 IncludePip=1
  del "%TEMP%\py_install.exe" >nul 2>&1
  powershell -NoProfile -Command "$env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + $env:Path"
)
where python >nul 2>&1 || ( echo [!] Python still missing. Restart PC and retry. pause & exit /b 1 )

echo [2/6] Installing the agent (one time)...
if not exist ".venv" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
if not exist ".env" copy .env.example .env >nul

echo [3/6] Installing Ollama (private/local AI)...
set "OLLAMA_DIR=%LOCALAPPDATA%\Programs\Ollama"
set "OLLAMA_EXE=%OLLAMA_DIR%\ollama.exe"
set "OLLAMA_ENGINE=%OLLAMA_DIR%\llama-server.exe"
if not exist "%OLLAMA_EXE%" goto :install_ollama
if not exist "%OLLAMA_ENGINE%" goto :install_ollama
goto :ollama_ready

:install_ollama
echo       Ollama engine missing - reinstalling cleanly...
taskkill /f /im ollama.exe >nul 2>&1
taskkill /f /im llama-server.exe >nul 2>&1
if exist "%OLLAMA_DIR%" rmdir /s /q "%OLLAMA_DIR%" >nul 2>&1
powershell -NoProfile -Command "Invoke-WebRequest 'https://ollama.com/download/OllamaSetup.exe' -OutFile \"$env:TEMP\OllamaSetup.exe\""
start /wait "" "%TEMP%\OllamaSetup.exe" /S
del "%TEMP%\OllamaSetup.exe" >nul 2>&1
set "OLLAMA_EXE=%OLLAMA_DIR%\ollama.exe"

:ollama_ready
if not exist "%OLLAMA_EXE%" set "OLLAMA_EXE=ollama"
start "" "%OLLAMA_EXE%" serve >nul 2>&1
timeout /t 6 >nul
echo       Verifying / pulling model llama3.1...
"%OLLAMA_EXE%" pull llama3.1

echo [4/6] Creating Desktop shortcut (future 1-click launch)...
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $p=[Environment]::GetFolderPath('Desktop')+'\MarketingOps Agent.lnk'; $s=$ws.CreateShortcut($p); $s.TargetPath='%~dp0tunnel.bat'; $s.WorkingDirectory='%CD%'; $s.Description='MarketingOps Agent - public link'; $s.Save()"

echo [5/6] Launching your public link...
start "" tunnel.bat

echo.
echo [6/6] DONE. Wait for the https://....trycloudflare.com link in the tunnel window,
echo        then open it on your phone or any computer. That's the agent.
echo        (To stop: double-click stop.bat. To relaunch later: double-click the Desktop shortcut.)
echo.
pause
