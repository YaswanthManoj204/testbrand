#!/usr/bin/env bash
# ==============================================================================
# BrandNest Development Server & Auto-Tunnel Runner
# Ensures Django and Cloudflare tunnel always start cleanly and shut down together.
# ==============================================================================

set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Ensure venv exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Virtual environment not found. Please create it first: python3 -m venv venv"
    exit 1
fi

PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"

# Clean up any leftover processes
cleanup() {
    echo ""
    echo "Stopping BrandNest server..."
    PYTHONPATH="$PROJECT_ROOT/backend" "$PYTHON_BIN" -c "from apps.frontend import tunnel; tunnel.stop_tunnel()" 2>/dev/null || true
    echo "Shutdown complete."
    exit 0
}

trap cleanup INT TERM EXIT

echo "=========================================================="
echo " Starting BrandNest Digital Business Card & Web Platform "
echo "=========================================================="

# Ensure database migrations are up to date
"$PYTHON_BIN" "$PROJECT_ROOT/backend/manage.py" migrate --noinput

# Detect Wi-Fi / Local Network IP for reliable phone scanning without Cloudflare
LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")

echo ""
echo "----------------------------------------------------------"
echo "  Local Web App:     http://127.0.0.1:8000"
if [ "$LAN_IP" != "127.0.0.1" ]; then
    echo "  Mobile Scan URL:   http://${LAN_IP}:8000"
    echo "  (Mobile phones on your Wi-Fi scan QR codes directly)"
fi
echo "  QR Generator:      Native Python 'qrcode' (No Cloudflare errors)"
echo "----------------------------------------------------------"
echo "Press Ctrl+C to stop the server cleanly."
echo ""

# Run Django on 0.0.0.0:8000 so both localhost and mobile devices on Wi-Fi can connect
exec "$PYTHON_BIN" "$PROJECT_ROOT/backend/manage.py" runserver 0.0.0.0:8000

