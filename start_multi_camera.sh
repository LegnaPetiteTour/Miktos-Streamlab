#!/bin/bash

# StreamLab Multi-Camera System Launcher
# Starts all necessary components for multi-camera production

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=================================================="
echo "📹 StreamLab Multi-Camera System"
echo "=================================================="
echo ""

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "✅ Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    echo "   Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install websockets tkinter
fi

echo ""
echo "Starting components..."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all components..."
    jobs -p | xargs kill 2>/dev/null || true
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check what to start
MODE="${1:-full}"

case "$MODE" in
    "receiver")
        echo "📡 Starting Multi-Camera Receiver only..."
        python3 "$SCRIPT_DIR/multi_camera_receiver.py" 8554 3
        ;;
    
    "director")
        echo "🎬 Starting Director UI only..."
        cd "$SCRIPT_DIR/Desktop/Backend/remote_control"
        python3 multi_camera_director.py
        ;;
    
    "server")
        echo "🌐 Starting Remote Control Server only..."
        cd "$SCRIPT_DIR/Desktop/Backend/remote_control"
        python3 websocket_server.py
        ;;
    
    "full")
        echo "🚀 Starting full multi-camera system..."
        echo ""
        
        # Start remote control server
        echo "1️⃣  Starting Remote Control Server (ports 9000-9001)..."
        cd "$SCRIPT_DIR/Desktop/Backend/remote_control"
        python3 websocket_server.py > /tmp/streamlab_server.log 2>&1 &
        SERVER_PID=$!
        sleep 2
        
        # Start multi-camera receiver
        echo "2️⃣  Starting Multi-Camera Receiver (ports 8554-8556)..."
        cd "$SCRIPT_DIR"
        python3 multi_camera_receiver.py 8554 3 > /tmp/streamlab_receiver.log 2>&1 &
        RECEIVER_PID=$!
        sleep 2
        
        # Start director UI
        echo "3️⃣  Starting Director UI..."
        cd "$SCRIPT_DIR/Desktop/Backend/remote_control"
        python3 multi_camera_director.py
        
        # Wait for user to exit
        wait $SERVER_PID $RECEIVER_PID
        ;;
    
    *)
        echo "❌ Unknown mode: $MODE"
        echo ""
        echo "Usage: $0 [mode]"
        echo ""
        echo "Modes:"
        echo "  full      - Start all components (default)"
        echo "  receiver  - Start only multi-camera receiver"
        echo "  director  - Start only director UI"
        echo "  server    - Start only remote control server"
        echo ""
        echo "Examples:"
        echo "  $0              # Start full system"
        echo "  $0 receiver     # Start only receiver"
        echo "  $0 director     # Start only director UI"
        exit 1
        ;;
esac
