#!/bin/bash
#
# Start Miktos StreamLab Control Panel
# This script starts both the WebSocket server and the web control panel
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Miktos StreamLab - Remote Control System${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Navigate to remote_control directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
if [ -f "../../../.venv/bin/activate" ]; then
    source "../../../.venv/bin/activate"
else
    echo "Error: Virtual environment not found!"
    echo "Please create it first: python3 -m venv .venv"
    exit 1
fi

# Check if required packages are installed
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
python3 -c "import flask, flask_socketio, websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing missing dependencies..."
    pip install flask flask-socketio flask-cors websockets
fi

echo ""
echo -e "${GREEN}✅ Dependencies OK${NC}"
echo ""
echo -e "${BLUE}Starting servers...${NC}"
echo ""

# Start WebSocket server in background
echo -e "${YELLOW}🎥 Starting WebSocket server (port 9000-9001)...${NC}"
python3 websocket_server.py &
WS_PID=$!
sleep 2

# Start Flask control panel
echo -e "${YELLOW}🌐 Starting web control panel (port 8080)...${NC}"
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Control Panel Ready!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${GREEN}📱 Camera Server:${NC}     ws://0.0.0.0:9000"
echo -e "${GREEN}🖥️  Controller Server:${NC}  ws://0.0.0.0:9001"
echo -e "${GREEN}🌐 Web Interface:${NC}     http://localhost:8080"
echo ""
echo -e "${BLUE}Open your browser to: ${GREEN}http://localhost:8080${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Start Flask (this will block)
python3 control_panel.py

# Cleanup on exit
trap "echo 'Stopping servers...'; kill $WS_PID 2>/dev/null; exit" INT TERM EXIT
