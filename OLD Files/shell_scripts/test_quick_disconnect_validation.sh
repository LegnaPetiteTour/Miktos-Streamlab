#!/bin/bash
# 🧪 QUICK DISCONNECT DETECTION VALIDATION
# Shorter test to validate the advanced disconnect detection system

set -e

echo "🧪 QUICK DISCONNECT DETECTION VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
TEST_IP="192.168.2.36"  # Local machine IP
TEST_PORT="8554"
TEST_DURATION=30        # 30 seconds total test
DISCONNECT_AT=15        # Disconnect at 15 seconds

echo "📋 Test Configuration:"
echo "   Target: $TEST_IP:$TEST_PORT"
echo "   Test duration: $TEST_DURATION seconds"
echo "   Disconnect simulation: $DISCONNECT_AT seconds"
echo ""

# Check device connection
if ! adb devices | grep -q "device$"; then
    echo "❌ ERROR: No Android device connected"
    exit 1
fi
echo "✅ Android device connected"

# Check app installation
if ! adb shell pm list packages | grep -q "com.miktos.streamlabcamera"; then
    echo "❌ ERROR: StreamLab Camera app not installed"
    exit 1
fi
echo "✅ StreamLab Camera app installed"

echo ""
echo "🚀 STARTING QUICK VALIDATION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create log files
TEST_START=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/tmp/quick_validation_$TEST_START.log"

echo "📱 Step 1: Prepare app for manual streaming..."
adb shell am start -n com.miktos.streamlabcamera/.MainActivity
echo ""
echo "📝 MANUAL STEPS REQUIRED:"
echo "   1. On your Android device, enter IP: $TEST_IP"
echo "   2. Enter Port: $TEST_PORT"  
echo "   3. Tap 'START STREAMING' button"
echo "   4. Wait for 'Streaming...' status"
echo ""

read -p "Press Enter when streaming is ACTIVE and confirmed..."

echo ""
echo "📡 Step 2: Starting log monitoring..."

# Start logcat in background
adb logcat -c
adb logcat -s "CameraStreamer" > "$LOG_FILE" &
LOGCAT_PID=$!

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    kill "$LOGCAT_PID" 2>/dev/null || true
    kill $(pgrep -f "python3 tcp_h264_receiver.py") 2>/dev/null || true
    echo "✅ Cleanup complete"
}
trap cleanup EXIT

echo "⏱️  Step 3: Monitoring for $DISCONNECT_AT seconds..."

# Let it stream for a bit
sleep "$DISCONNECT_AT"

echo ""
echo "🔌 Step 4: Simulating disconnect (killing receiver)..."
DISCONNECT_TIME=$(date +%s)

# Kill any running receivers
kill $(pgrep -f "python3 tcp_h264_receiver.py") 2>/dev/null || echo "No receiver process found"

echo "   Disconnect initiated at: $(date)"
echo "   Monitoring for disconnect detection..."

# Wait for detection
DETECTION_TIME=""
START_MONITOR=$(date +%s)

echo "⏳ Waiting up to 15 seconds for disconnect detection..."
while [ $(($(date +%s) - START_MONITOR)) -lt 15 ]; do
    if grep -q "Socket disconnected\|Encoder stall detected\|❌" "$LOG_FILE" 2>/dev/null; then
        DETECTION_TIME=$(($(date +%s) - DISCONNECT_TIME))
        break
    fi
    sleep 0.5
done

echo ""
echo "📊 QUICK VALIDATION RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$DETECTION_TIME" ]; then
    echo "✅ DISCONNECT DETECTED in $DETECTION_TIME seconds"
    
    if [ "$DETECTION_TIME" -le 10 ]; then
        echo "🎯 SUCCESS: Detection time ($DETECTION_TIME s) ≤ Expected (10 s)"
        
        # Check for auto-reconnection
        if grep -q "Auto-reconnecting\|🚀 Attempting auto-reconnection" "$LOG_FILE" 2>/dev/null; then
            echo "🔄 BONUS: Auto-reconnection system activated"
            RESULT="EXCELLENT"
        else
            RESULT="GOOD"
        fi
    else
        echo "⚠️  WARNING: Detection time ($DETECTION_TIME s) > Expected (10 s)"
        RESULT="SLOW"
    fi
else
    echo "❌ FAILURE: No disconnect detected within 15 seconds"
    RESULT="FAIL"
fi

echo ""
echo "📋 Android Log Analysis:"
if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 CameraStreamer Log Output:"
    cat "$LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ No CameraStreamer logs captured - streaming may not have started"
    RESULT="NO_LOGS"
fi

echo ""
echo "🏁 QUICK VALIDATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Result: $RESULT"
echo "Detection Time: ${DETECTION_TIME:-"N/A"} seconds"
echo "Log File: $LOG_FILE"
echo ""

case "$RESULT" in
    "EXCELLENT")
        echo "🎉 OUTSTANDING - Disconnect detection AND auto-reconnection working!"
        exit 0
        ;;
    "GOOD")
        echo "✅ GOOD - Disconnect detection working as expected!"
        exit 0
        ;;
    "SLOW")
        echo "⚠️  WARNING - Detection works but slower than optimal"
        exit 1
        ;;
    "FAIL")
        echo "💥 FAILED - Disconnect detection not working"
        exit 2
        ;;
    "NO_LOGS")
        echo "❓ INCONCLUSIVE - No streaming logs detected"
        exit 3
        ;;
esac