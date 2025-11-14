#!/bin/bash
# 🧪 DISCONNECT DETECTION TIMING VALIDATION TEST
# Validates that encoder stall detection triggers within 10 seconds of data stoppage

set -e

echo "🧪 DISCONNECT DETECTION TIMING VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration
TEST_IP="192.168.2.36"  # Local machine IP with receiver
TEST_PORT="8554"
EXPECTED_DETECTION_TIME=10  # seconds
TEST_DURATION=15           # seconds (should detect within 10)

echo "📋 Test Configuration:"
echo "   Target: $TEST_IP:$TEST_PORT"
echo "   Expected detection time: ≤ $EXPECTED_DETECTION_TIME seconds"
echo "   Test duration: $TEST_DURATION seconds"
echo ""

# Check if receiver is running
echo "🔍 Checking if TCP receiver is available..."
if ! nc -z "$TEST_IP" "$TEST_PORT" 2>/dev/null; then
    echo "❌ ERROR: No receiver found at $TEST_IP:$TEST_PORT"
    echo "   Please start the TCP H.264 receiver first:"
    echo "   python3 tcp_h264_receiver.py"
    exit 1
fi
echo "✅ Receiver is available"
echo ""

# Check if Android app is installed
echo "🔍 Checking Android app installation..."
if ! adb shell pm list packages | grep -q "com.miktos.streamlabcamera"; then
    echo "❌ ERROR: Miktos StreamLab Camera app not installed"
    echo "   Please install the app first:"
    echo "   cd /Users/atorrella/Desktop/Miktos/Mobile/Android"
    echo "   ./gradlew installDebug"
    exit 1
fi
echo "✅ Android app is installed"
echo ""

echo "🚀 STARTING DISCONNECT DETECTION TIMING TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create temporary log file
LOG_FILE="/tmp/disconnect_test_$(date +%Y%m%d_%H%M%S).log"

echo "📱 Step 1: Starting Android streaming..."
echo "   Logs will be captured to: $LOG_FILE"

# Start Android logcat capture in background
adb logcat -c  # Clear existing logs
adb logcat -s "CameraStreamer" > "$LOG_FILE" &
LOGCAT_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    kill "$LOGCAT_PID" 2>/dev/null || true
    adb shell am force-stop com.miktos.streamlabcamera 2>/dev/null || true
    echo "✅ Cleanup complete"
}
trap cleanup EXIT

echo "   Starting StreamLab Camera app..."
adb shell am start -n com.miktos.streamlabcamera/.MainActivity

sleep 3

echo "   Initiating stream to $TEST_IP:$TEST_PORT..."
# Simulate button press to start streaming
# Note: This requires the app to auto-connect or manual intervention
adb shell input tap 540 1200  # Approximate start button location

echo "⏱️  Step 2: Waiting for stream establishment..."
sleep 5

echo "🔌 Step 3: Simulating network disconnect (closing receiver)..."
DISCONNECT_START=$(date +%s)
echo "   Disconnect initiated at: $(date)"

# Kill the receiver to simulate network disconnect
pkill -f "tcp_h264_receiver.py" || echo "   (Receiver may not be running as Python process)"

echo ""
echo "⏳ Step 4: Monitoring for disconnect detection..."
echo "   Waiting up to $TEST_DURATION seconds for detection..."

# Monitor logs for disconnect detection
DETECTION_TIME=""
START_TIME=$(date +%s)

while [ $(($(date +%s) - START_TIME)) -lt $TEST_DURATION ]; do
    if grep -q "Encoder stall detected\|Socket disconnected" "$LOG_FILE" 2>/dev/null; then
        DETECTION_TIME=$(($(date +%s) - DISCONNECT_START))
        break
    fi
    sleep 0.5
done

echo ""
echo "📊 TEST RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$DETECTION_TIME" ]; then
    echo "✅ DISCONNECT DETECTED in $DETECTION_TIME seconds"
    
    if [ "$DETECTION_TIME" -le "$EXPECTED_DETECTION_TIME" ]; then
        echo "🎯 SUCCESS: Detection time ($DETECTION_TIME s) ≤ Expected ($EXPECTED_DETECTION_TIME s)"
        TEST_RESULT="PASS"
    else
        echo "⚠️  WARNING: Detection time ($DETECTION_TIME s) > Expected ($EXPECTED_DETECTION_TIME s)"
        TEST_RESULT="SLOW"
    fi
else
    echo "❌ FAILURE: No disconnect detected within $TEST_DURATION seconds"
    TEST_RESULT="FAIL"
fi

echo ""
echo "📋 Detailed Logs:"
if [ -f "$LOG_FILE" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ No logs captured"
fi

echo ""
echo "🏁 TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Result: $TEST_RESULT"
echo "Detection Time: ${DETECTION_TIME:-"N/A"} seconds"
echo "Expected Time: ≤ $EXPECTED_DETECTION_TIME seconds"
echo "Log File: $LOG_FILE"
echo ""

case "$TEST_RESULT" in
    "PASS")
        echo "🎉 VALIDATION SUCCESSFUL - Disconnect detection working as expected!"
        exit 0
        ;;
    "SLOW")
        echo "⚠️  VALIDATION WARNING - Detection works but slower than expected"
        exit 1
        ;;
    "FAIL")
        echo "💥 VALIDATION FAILED - Disconnect detection not working properly"
        exit 2
        ;;
esac