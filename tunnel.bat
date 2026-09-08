@echo off
REM ============================================================================
REM  MarketingOps Agent - PUBLIC TUNNEL (anywhere access)
REM  Double-click this. It starts the agent and prints a public https link you
REM  can open on ANY phone/computer with internet. Keep this window open.
REM  NOTE: set WEB_PASSWORD in .env first, or anyone can open it.
REM ============================================================================
setlocal
cd /d "%~dp0"

REM free port 8000 if an old server is still running
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

REM start the agent server using the project's virtual environment
start "MarketingOps Agent" /min .venv\Scripts\python cli.py web
powershell -NoProfile -Command "$n=0; while($n -lt 60){ try { if((Invoke-WebRequest http://localhost:8000/api/status -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200){ break } } catch {} ; Start-Sleep -Seconds 1; $n++ }"

REM try cloudflared (downloads from GitHub, which may be blocked here)
if not exist "cloudflared.exe" (
  echo [*] Fetching public tunnel tool (cloudflared)...
  powershell -NoProfile -Command "try { Invoke-WebRequest 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe' -TimeoutSec 25 -ErrorAction Stop } catch { Write-Host '  cloudflared download failed (GitHub blocked?).' }"
)
if exist "cloudflared.exe" (
  echo.
  echo [*] Starting public tunnel. The https link below works on any device, anywhere.
  echo.
  cloudflared tunnel --url http://localhost:8000
  exit /b 0
)

REM fallback: ssh tunnel via localhost.run (built-in OpenSSH, no download needed)
where ssh >nul 2>&1
if not errorlevel 1 (
  echo.
  echo [*] Starting public tunnel via localhost.run (ssh). The URL below works anywhere.
  echo.
  ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 nokey@localhost.run
  exit /b 0
)

echo.
echo [!] Could not create a public tunnel (GitHub blocked and ssh unavailable).
echo     Use the agent on THIS PC at:  http://localhost:8000
powershell -NoProfile -Command "Write-Host '     Your LAN IP(s):' ; (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notmatch 'Loopback'}).IPAddress"
echo     On your phone (same WiFi):    http://<LAN-IP>:8000
echo     For true anywhere access, deploy to a free host (Render/Railway) - I can set that up.
echo.
echo     The agent server is running. Close its window or run stop.bat to stop.
pause
