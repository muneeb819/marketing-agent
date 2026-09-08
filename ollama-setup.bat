@echo off
REM ============================================================================
REM  Ollama one-time setup (Windows) - double-click. Installs Ollama, starts it,
REM  and downloads the model. After this, the agent works fully offline/private.
REM ============================================================================
setlocal
cd /d "%~dp0"

echo [*] Downloading Ollama installer...
powershell -NoProfile -Command "Invoke-WebRequest 'https://ollama.com/download/OllamaSetup.exe' -OutFile \"$env:TEMP\OllamaSetup.exe\""
if not exist "%TEMP%\OllamaSetup.exe" (
  echo [!] Download failed. Check your internet and retry.
  pause
  exit /b 1
)

echo [*] Installing Ollama (silent)...
start /wait "" "%TEMP%\OllamaSetup.exe" /S
del "%TEMP%\OllamaSetup.exe" >nul 2>&1

REM locate the ollama CLI
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not exist "%OLLAMA_EXE%" set "OLLAMA_EXE=ollama"

echo [*] Starting Ollama...
start "" "%OLLAMA_EXE%" serve >nul 2>&1
timeout /t 6 >nul

echo [*] Pulling model llama3.1 (one time, ~4 GB)...
"%OLLAMA_EXE%" pull llama3.1

echo.
echo Done. Ollama is installed and running. Now double-click:
echo    - tunnel.bat   (to open on your phone / anywhere)
echo    - or start.bat (on this PC only)
echo.
pause
