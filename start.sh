#!/usr/bin/env bash
# ===========================================================================
#  MarketingOps Agent - ONE-CLICK LAUNCHER (Linux / macOS / Termux-Android)
#  Run:  bash start.sh
# ===========================================================================
set -e
cd "$(dirname "$0")"

# 1) Python check
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] Python 3.10+ not found. Install it, then re-run."
  exit 1
fi

# 2) Virtual environment (created once)
if [ ! -d ".venv" ]; then
  echo "[*] Creating isolated environment (one time)..."
  python3 -m venv .venv
fi

# 3) Activate + install dependencies
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 4) Default config if missing
if [ ! -f ".env" ]; then
  echo "[*] Creating default .env (LLM_PROVIDER=ollama)..."
  cp .env.example .env
fi

# 5) Launch web UI (wait until ready, then try to open a browser)
echo "[*] Starting the agent at http://localhost:8000 ..."
python cli.py web &
SERVER_PID=$!
n=0
while [ $n -lt 40 ]; do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/status 2>/dev/null | grep -q 200; then
    break
  fi
  sleep 1
  n=$((n+1))
done
# Try to open a browser; harmless if it fails (Termux/iOS)
(xdg-open http://localhost:8000 2>/dev/null || open http://localhost:8000 2>/dev/null || true)
echo
echo "   Open: http://localhost:8000   (server PID $SERVER_PID)"
echo "   - On your phone (same Wi-Fi): http://YOUR-DEVICE-IP:8000"
echo "   - If the page shows a yellow 'LLM not ready' banner, configure a key:  python cli.py init"
echo "   - To stop:  kill $SERVER_PID"
wait "$SERVER_PID"
