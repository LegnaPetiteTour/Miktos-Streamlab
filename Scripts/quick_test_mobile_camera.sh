#!/bin/bash
#
# Quick Test Script for Mobile Camera System
# Tests the complete flow: Mobile → Desktop → OBS
#

echo "=================================================="
echo "StreamLab Mobile Camera System - Quick Test"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

# Check FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✅ FFmpeg found${NC}"
    ffmpeg -version | head -n 1
else
    echo -e "${RED}❌ FFmpeg not found${NC}"
    echo "   Install: brew install ffmpeg"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python 3 found${NC}"
    python3 --version
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Check SRT support in FFmpeg
if ffmpeg -protocols 2>&1 | grep -q "srt"; then
    echo -e "${GREEN}✅ FFmpeg has SRT support${NC}"
else
    echo -e "${RED}❌ FFmpeg missing SRT support${NC}"
    echo "   Reinstall: brew reinstall ffmpeg"
    exit 1
fi

echo ""
echo "=================================================="
echo "Step 2: Find your desktop IP address"
echo "=================================================="
echo ""

# Get IP address (macOS specific)
if [[ "$OSTYPE" == "darwin"* ]]; then
    IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
    echo "Your desktop IP: $IP"
    echo ""
    echo -e "${YELLOW}⚠️  Enter this IP in your mobile app${NC}"
else
    echo "Manual IP detection needed for your OS"
    echo "Run: ifconfig (Linux/macOS) or ipconfig (Windows)"
fi

echo ""
echo "=================================================="
echo "Step 3: Starting desktop SRT receiver"
echo "=================================================="
echo ""

PORT=9001
echo "Starting receiver on port $PORT..."
echo ""
echo -e "${GREEN}Instructions for mobile app:${NC}"
echo "  1. Open StreamLab Camera app on iPhone"
echo "  2. Enter desktop IP: $IP"
echo "  3. Enter port: $PORT"
echo "  4. Press 'START STREAMING'"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the receiver${NC}"
echo ""
echo "=================================================="
echo ""

# Start the receiver
python3 -m src.mobile.srt_receiver --port $PORT --output window

echo ""
echo "Receiver stopped."
