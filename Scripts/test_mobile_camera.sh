#!/bin/bash

# Test Mobile Camera System

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              Testing Mobile Camera System                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Activate Python environment
source venv/bin/activate

# Start SRT receiver
echo "Starting SRT receiver on port 9001..."
echo "Waiting for mobile camera connection..."
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m src.mobile.srt_receiver --port 9001 --mode window
