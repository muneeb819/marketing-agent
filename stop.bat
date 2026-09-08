@echo off
REM Stop the MarketingOps Agent server.
taskkill /f /im python.exe >nul 2>&1
echo Agent stopped.
pause
