#!/bin/bash
#
# SRT Backup Receiver Test Script
# Receives SRT stream on port 9000 and saves to file for testing
#

set -e

PORT="${1:-9000}"
OUTPUT_FILE="srt_backup_test_$(date +%Y%m%d_%H%M%S).ts"

echo "============================================="
echo "SRT Backup Receiver Test"
echo "============================================="
echo "Listening on port: $PORT"
echo "Output file: $OUTPUT_FILE"
echo ""
echo "This will receive the SRT backup stream when"
echo "the failover system activates."
echo ""
echo "Press Ctrl+C to stop"
echo "============================================="
echo ""

# Start SRT receiver in listener mode
srt-live-transmit \
    "srt://:${PORT}?mode=listener" \
    "file://${OUTPUT_FILE}" \
    -v

echo ""
echo "Stream saved to: $OUTPUT_FILE"
