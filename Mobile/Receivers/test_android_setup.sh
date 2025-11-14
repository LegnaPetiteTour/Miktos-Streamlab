#!/bin/bash
# Quick test to verify Android development environment is ready

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         Android Development Environment Check                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check Java
echo "1️⃣  Checking Java..."
if java -version 2>&1 | grep -q "17"; then
    echo "   ✅ Java 17 installed"
    java -version 2>&1 | head -n 1
else
    echo "   ❌ Java 17 not found"
    exit 1
fi
echo ""

# Check Android SDK
echo "2️⃣  Checking Android SDK..."
if [ -d "$ANDROID_HOME" ]; then
    echo "   ✅ ANDROID_HOME set: $ANDROID_HOME"
    ls -1 "$ANDROID_HOME/platforms" 2>/dev/null | head -n 3
else
    echo "   ❌ ANDROID_HOME not set"
    exit 1
fi
echo ""

# Check ADB
echo "3️⃣  Checking ADB..."
if command -v adb &> /dev/null; then
    echo "   ✅ ADB installed"
    adb --version | head -n 1
else
    echo "   ❌ ADB not found"
    exit 1
fi
echo ""

# Check phone connection
echo "4️⃣  Checking phone connection..."
DEVICE_COUNT=$(adb devices | grep -c "device$")
if [ "$DEVICE_COUNT" -gt 0 ]; then
    echo "   ✅ Samsung S23 FE connected"
    adb devices | grep "device$"
else
    echo "   ⚠️  No devices connected"
    echo "   Connect your Samsung S23 FE via USB"
fi
echo ""

# Check FFmpeg
echo "5️⃣  Checking FFmpeg (for receiver)..."
if command -v ffplay &> /dev/null; then
    echo "   ✅ FFplay installed"
    ffplay -version 2>&1 | head -n 1
else
    echo "   ⚠️  FFplay not found"
    echo "   Install with: brew install ffmpeg"
fi
echo ""

# Check project
echo "6️⃣  Checking Android project..."
if [ -d "StreamLabCameraAndroid/app/src/main/java" ]; then
    echo "   ✅ Project structure created"
    echo "   Files:"
    find StreamLabCameraAndroid/app/src/main/java -name "*.kt" | wc -l | xargs echo "      Kotlin files:"
else
    echo "   ❌ Project not found"
    exit 1
fi
echo ""

# Get Mac IP
echo "7️⃣  Your Mac IP addresses:"
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print "   ", $2}'
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    READY TO BUILD! ✅                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. cd 'StreamLabCameraAndroid'"
echo "  2. open -a 'Android Studio' ."
echo "  3. Wait for Gradle sync"
echo "  4. Click Run ▶️"
echo ""
