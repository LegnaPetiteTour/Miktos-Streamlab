#!/bin/bash
#
# Miktos Hub - Quick Start Script
# Starts all necessary services for hardware testing
#

set -e

echo "🚀 MIKTOS HUB - QUICK START"
echo "=" | awk '{for(i=1;i<=70;i++) printf "="; printf "\n"}'

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="/Users/atorrella/Desktop/Miktos Streamlab"
HUB_DIR="$BASE_DIR/Miktos Hub"
VENV_DIR="$BASE_DIR/.venv"

echo ""
echo "📋 Configuration:"
echo "   Base: $BASE_DIR"
echo "   Hub:  $HUB_DIR"
echo "   Venv: $VENV_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "   Expected: $VENV_DIR"
    exit 1
fi

# Activate virtual environment
echo ""
echo "🐍 Activating Python environment..."
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✅ Python environment active${NC}"

# Get Mac IP address
MAC_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo ""
echo "🌐 Network Information:"
echo "   Mac IP: $MAC_IP"
echo "   Hub URL: http://$MAC_IP:8000"
echo "   Local URL: http://127.0.0.1:8000"

# Check if OBS is running
echo ""
echo "🎬 Checking OBS Studio..."
if pgrep -x "OBS" > /dev/null; then
    echo -e "${GREEN}✅ OBS is running${NC}"
else
    echo -e "${YELLOW}⚠️  OBS is not running${NC}"
    echo "   Launch OBS: open -a OBS"
    echo "   Enable WebSocket: Tools → WebSocket Server Settings"
fi

# Kill any existing server
echo ""
echo "🧹 Cleaning up old processes..."
pkill -f "uvicorn api.server" 2>/dev/null && echo "   Killed old server" || echo "   No old server found"

# Start the server
echo ""
echo "🚀 Starting Miktos Hub server..."
cd "$HUB_DIR"

# Start in background and log to file
LOG_FILE="/tmp/miktos_server.log"
nohup python -m uvicorn api.server:create_app \
    --factory \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    > "$LOG_FILE" 2>&1 &

SERVER_PID=$!
echo "   Server PID: $SERVER_PID"
echo "   Log file: $LOG_FILE"

# Wait for server to start
echo ""
echo "⏳ Waiting for server to start..."
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✅ Server is running!${NC}"
    
    # Test the health endpoint
    if curl -s http://127.0.0.1:8000/api/health/metrics > /dev/null; then
        echo -e "${GREEN}✅ Server is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Server started but not responding yet${NC}"
        echo "   Waiting a bit longer..."
        sleep 5
    fi
else
    echo -e "${RED}❌ Server failed to start${NC}"
    echo "   Check logs: tail -50 $LOG_FILE"
    exit 1
fi

# Display status
echo ""
echo "=" | awk '{for(i=1;i<=70;i++) printf "="; printf "\n"}'
echo -e "${GREEN}✅ MIKTOS HUB IS READY${NC}"
echo "=" | awk '{for(i=1;i<=70;i++) printf "="; printf "\n"}'

echo ""
echo "📱 Phone Setup:"
echo "   1. Connect phone to same WiFi network"
echo "   2. Open Miktos StreamLab app"
echo "   3. Enter Hub IP: $MAC_IP"
echo "   4. Tap 'Connect to Hub'"

echo ""
echo "🎬 OBS Setup (if not running):"
echo "   1. Launch: open -a OBS"
echo "   2. Tools → WebSocket Server Settings"
echo "   3. Enable WebSocket, Port: 4455"
echo "   4. Apply and OK"

echo ""
echo "🔗 Useful URLs:"
echo "   API Docs:  http://127.0.0.1:8000/docs"
echo "   Health:    http://127.0.0.1:8000/api/health/metrics"
echo "   Cameras:   http://127.0.0.1:8000/api/cameras"
echo "   Scenes:    http://127.0.0.1:8000/api/scenes"

echo ""
echo "🧪 Testing Commands:"
echo "   Test OBS:     python test_obs_connection.py"
echo "   Test Camera:  python test_camera_discovery.py"
echo "   View logs:    tail -f $LOG_FILE"
echo "   Stop server:  pkill -f 'uvicorn api.server'"

echo ""
echo "🎯 Quick Tests:"
echo "   # Test OBS connection"
echo "   cd '$BASE_DIR' && python test_obs_connection.py"
echo ""
echo "   # Wait for cameras"
echo "   cd '$BASE_DIR' && python test_camera_discovery.py"

echo ""
echo "📊 Monitor server logs in real-time:"
echo "   tail -f $LOG_FILE | grep -E '(ERROR|camera|scene|stream)'"

echo ""
echo -e "${GREEN}Happy testing! 🚀${NC}"
echo ""
