#!/bin/bash
# Quick start script for StreamLab Mobile Camera Receiver

echo "🎥 StreamLab Mobile Camera Receiver"
echo "===================================="
echo ""

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg not found!"
    echo ""
    echo "Please install FFmpeg with SRT support:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux: apt-get install ffmpeg"
    echo ""
    exit 1
fi

# Check for SRT support
if ! ffmpeg -protocols 2>&1 | grep -q "srt"; then
    echo "⚠️  Warning: FFmpeg may not have SRT support"
    echo "   If streaming fails, reinstall FFmpeg with SRT"
    echo ""
fi

echo "✅ FFmpeg found with SRT support"
echo ""

# Get desktop IP
echo "📡 Your desktop IP addresses:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print "   "$2}'
else
    # Linux
    ip addr show | grep "inet " | grep -v 127.0.0.1 | awk '{print "   "$2}' | cut -d/ -f1
fi

echo ""
echo "📱 Configure mobile app with one of these IPs and port 9001"
echo ""
echo "Starting receiver..."
echo "Press Ctrl+C to stop"
echo ""
echo "===================================="
echo ""

# Start receiver
python3 -m src.mobile.srt_receiver --port 9001 --output window
