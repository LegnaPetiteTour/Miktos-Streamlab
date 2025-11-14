#!/bin/bash

# Miktos Streamlab - Desktop SRT Receiver
# Receives camera stream from iPhone and displays it

set -e

PORT="${1:-9001}"
WINDOW_TITLE="MobileCamera_Port${PORT}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          Miktos Streamlab - Mobile Camera Receiver            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📡 Waiting for mobile camera on port $PORT..."
echo "   Window title: $WINDOW_TITLE"
echo ""
echo "💡 On your iPhone:"
echo "   1. Enter this Mac's IP address"
echo "   2. Port: $PORT"
echo "   3. Tap START STREAMING"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Check if FFmpeg with SRT support is installed
if ! ffmpeg -version 2>/dev/null | grep -q "enable-libsrt"; then
    echo "❌ Error: FFmpeg with SRT support not found"
    echo ""
    echo "Install with: brew install ffmpeg"
    exit 1
fi

# Get this machine's IP addresses
echo "📍 This Mac's IP addresses:"
ifconfig | grep "inet " | grep -v "127.0.0.1" | awk '{print "   " $2}'
echo ""

# Start SRT listener with FFmpeg
ffmpeg \
    -hide_banner \
    -loglevel info \
    -protocol_whitelist "file,udp,rtp,tcp" \
    -i "srt://0.0.0.0:${PORT}?mode=listener&latency=80" \
    -f sdl \
    -window_title "${WINDOW_TITLE}" \
    -
