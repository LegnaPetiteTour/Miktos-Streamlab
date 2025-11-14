#!/bin/bash
# Quick Verification - Check if fixes are working
# Run this BEFORE spending time on mobile app rebuild

echo "🔍 Verifying Fixes Applied..."
echo ""

# Test 1: Check Python import
echo "[1/3] Testing Python import fix..."
cd "$(dirname "$0")"
python3 -c "from src.mobile import SRTReceiver; print('✅ Python import working')" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Python fix verified"
else
    echo "❌ Python import still failing"
    exit 1
fi
echo ""

# Test 2: Check FFmpeg
echo "[2/3] Checking FFmpeg SRT support..."
if ffmpeg -version 2>&1 | grep -q "libsrt"; then
    echo "✅ FFmpeg with SRT found"
else
    echo "❌ FFmpeg missing SRT support"
    echo "   Run: brew reinstall ffmpeg"
    exit 1
fi
echo ""

# Test 3: Check Podfile
echo "[3/3] Checking Podfile Swift settings..."
if grep -q "SWIFT_VERSION.*5.0" StreamLabCamera/ios/Podfile; then
    echo "✅ Podfile has Swift 5.0 fix"
else
    echo "❌ Podfile not updated correctly"
    exit 1
fi
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              All Fixes Verified! ✅                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Python import: WORKING"
echo "✅ FFmpeg SRT: WORKING"  
echo "✅ Swift 5 fix: APPLIED"
echo ""
echo "🚀 You're ready to:"
echo "   1. Run ./test_mobile_camera.sh to test desktop receiver"
echo "   2. Run ./fix_mobile_app.sh to rebuild mobile app"
echo ""
echo "📖 Read FIXES_APPLIED.md for detailed instructions"
