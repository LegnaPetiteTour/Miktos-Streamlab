#!/bin/bash
# 🔋 COMPREHENSIVE UNLOCK-AFTER-60-MINUTES FIELD TEST
# Validates the fix for the critical production disconnect bug

set -e

echo "🔋 UNLOCK-AFTER-60-MINUTES FIELD TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configuration  
TEST_IP="192.168.2.36"  # Local machine IP with receiver
TEST_PORT="8554"
TOTAL_TEST_MINUTES=70    # Total test duration
UNLOCK_MINUTE=65         # When to perform unlock test
VALIDATION_MINUTES=5     # Minutes to monitor after unlock

echo "📋 Test Configuration:"
echo "   Target: $TEST_IP:$TEST_PORT" 
echo "   Total test duration: $TOTAL_TEST_MINUTES minutes"
echo "   Unlock test at: $UNLOCK_MINUTE minutes"
echo "   Post-unlock validation: $VALIDATION_MINUTES minutes"
echo ""

# Pre-flight checks
echo "🔍 PRE-FLIGHT CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check ADB connection
if ! adb devices | grep -q "device$"; then
    echo "❌ ERROR: No Android device connected via ADB"
    echo "   Please connect device and enable USB debugging"
    exit 1
fi
echo "✅ Android device connected"

# Check receiver availability
if ! nc -z "$TEST_IP" "$TEST_PORT" 2>/dev/null; then
    echo "❌ ERROR: No receiver found at $TEST_IP:$TEST_PORT"
    echo "   Please start the TCP H.264 receiver first:"
    echo "   python3 tcp_h264_receiver.py"
    exit 1
fi
echo "✅ TCP receiver is available"

# Check app installation
if ! adb shell pm list packages | grep -q "com.miktos.streamlabcamera"; then
    echo "❌ ERROR: Miktos StreamLab Camera app not installed"
    echo "   Please install the app first"
    exit 1
fi
echo "✅ StreamLab Camera app installed"

# Check battery level
BATTERY_LEVEL=$(adb shell dumpsys battery | grep level | cut -d: -f2 | tr -d ' ')
if [ "$BATTERY_LEVEL" -lt 30 ]; then
    echo "⚠️  WARNING: Battery level is ${BATTERY_LEVEL}% - recommend charging above 30%"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Battery level: ${BATTERY_LEVEL}%"
fi

echo ""
echo "🚀 STARTING COMPREHENSIVE FIELD TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create test log files
TEST_START=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="/tmp/unlock_field_test_$TEST_START"
mkdir -p "$LOG_DIR"

MAIN_LOG="$LOG_DIR/field_test.log"
ANDROID_LOG="$LOG_DIR/android_logcat.log"
BATTERY_LOG="$LOG_DIR/battery_usage.log" 
NETWORK_LOG="$LOG_DIR/network_stats.log"

echo "📁 Logs directory: $LOG_DIR"

# Start monitoring in background
adb logcat -c
adb logcat -s "CameraStreamer" > "$ANDROID_LOG" &
LOGCAT_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up background processes..."
    kill "$LOGCAT_PID" 2>/dev/null || true
    adb shell am force-stop com.miktos.streamlabcamera 2>/dev/null || true
    echo "✅ Cleanup complete"
    echo "📁 Logs saved in: $LOG_DIR"
}
trap cleanup EXIT

# Log test start
{
    echo "UNLOCK-AFTER-60-MINUTES FIELD TEST"
    echo "Test started: $(date)"
    echo "Configuration: $TEST_IP:$TEST_PORT"
    echo "Target duration: $TOTAL_TEST_MINUTES minutes"
    echo "Unlock test at: $UNLOCK_MINUTE minutes"
    echo "Battery level at start: ${BATTERY_LEVEL}%"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
} > "$MAIN_LOG"

echo "📱 Starting StreamLab Camera application..."
adb shell am start -n com.miktos.streamlabcamera/.MainActivity

sleep 5

echo "🎥 Initiating streaming to $TEST_IP:$TEST_PORT..."
# Note: This may require manual intervention to start streaming
adb shell input tap 540 1200  # Approximate start button coordinates

sleep 3

# Verify streaming started
if ! grep -q "Streaming pipeline initialized" "$ANDROID_LOG" 2>/dev/null; then
    echo "⚠️  WARNING: Could not verify stream start from logs"
    echo "   Please manually verify streaming is active on the device"
    read -p "Press Enter when streaming is confirmed active..."
fi

echo ""
echo "⏱️  PHASE 1: CONTINUOUS STREAMING MONITORING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Monitor streaming for the specified duration
START_TIME=$(date +%s)
UNLOCK_TIME=$((START_TIME + UNLOCK_MINUTE * 60))
END_TIME=$((START_TIME + TOTAL_TEST_MINUTES * 60))

MINUTE_COUNTER=0
LAST_BATTERY_LOG=0

while [ $(date +%s) -lt $UNLOCK_TIME ]; do
    CURRENT_TIME=$(date +%s)
    ELAPSED_MINUTES=$(((CURRENT_TIME - START_TIME) / 60))
    
    # Update every minute
    if [ $ELAPSED_MINUTES -gt $MINUTE_COUNTER ]; then
        MINUTE_COUNTER=$ELAPSED_MINUTES
        
        # Log battery usage every 10 minutes
        if [ $((ELAPSED_MINUTES % 10)) -eq 0 ] && [ $ELAPSED_MINUTES -gt $LAST_BATTERY_LOG ]; then
            CURRENT_BATTERY=$(adb shell dumpsys battery | grep level | cut -d: -f2 | tr -d ' ')
            BATTERY_USED=$((BATTERY_LEVEL - CURRENT_BATTERY))
            RATE=$(echo "scale=2; $BATTERY_USED / $ELAPSED_MINUTES * 60" | bc -l 2>/dev/null || echo "N/A")
            
            echo "⚡ Minute $ELAPSED_MINUTES: Battery ${CURRENT_BATTERY}% (used ${BATTERY_USED}%, rate ${rate}%/hour)"
            echo "$(date): Minute $ELAPSED_MINUTES - Battery ${CURRENT_BATTERY}% (rate ${rate}%/hour)" >> "$BATTERY_LOG"
            
            LAST_BATTERY_LOG=$ELAPSED_MINUTES
        elif [ $((ELAPSED_MINUTES % 5)) -eq 0 ]; then
            echo "⏳ Minute $ELAPSED_MINUTES/$UNLOCK_MINUTE - Monitoring streaming..."
        fi
        
        # Check for disconnections
        if grep -q "Socket disconnected\|Encoder stall detected\|STREAM_DISCONNECTED" "$ANDROID_LOG" 2>/dev/null; then
            echo "❌ EARLY DISCONNECT DETECTED at minute $ELAPSED_MINUTES"
            echo "$(date): Early disconnect at minute $ELAPSED_MINUTES" >> "$MAIN_LOG"
            
            # Check if auto-reconnection worked
            if grep -q "Auto-reconnecting\|🚀 Attempting auto-reconnection" "$ANDROID_LOG" 2>/dev/null; then
                echo "🔄 Auto-reconnection system activated"
            fi
        fi
    fi
    
    sleep 30  # Check every 30 seconds
done

echo ""
echo "🔓 PHASE 2: CRITICAL UNLOCK TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

UNLOCK_START=$(date +%s)
echo "🔓 Performing unlock test at minute $UNLOCK_MINUTE..."
echo "$(date): UNLOCK TEST INITIATED at minute $UNLOCK_MINUTE" >> "$MAIN_LOG"

# Wake and unlock the device (simulate user unlock)
adb shell input keyevent KEYCODE_WAKEUP
sleep 1
adb shell input swipe 540 1500 540 500  # Swipe up to unlock
sleep 2
adb shell input keyevent KEYCODE_HOME    # Go to home screen
sleep 3
adb shell input keyevent KEYCODE_BACK    # Return to app

echo "   Device unlocked and returned to app"
echo "   Monitoring for disconnect detection..."

# Monitor for disconnect detection in the next few minutes  
VALIDATION_END=$((UNLOCK_START + VALIDATION_MINUTES * 60))
DISCONNECT_DETECTED=false

while [ $(date +%s) -lt $VALIDATION_END ]; do
    ELAPSED_SINCE_UNLOCK=$((($(date +%s) - UNLOCK_START)))
    
    if grep -q "Socket disconnected\|Encoder stall detected" "$ANDROID_LOG" 2>/dev/null; then
        if [ "$DISCONNECT_DETECTED" = false ]; then
            DISCONNECT_DETECTED=true
            echo "🎯 DISCONNECT DETECTED ${ELAPSED_SINCE_UNLOCK}s after unlock"
            echo "$(date): Disconnect detected ${ELAPSED_SINCE_UNLOCK}s after unlock" >> "$MAIN_LOG"
            
            # Monitor auto-reconnection
            sleep 5
            if grep -q "Auto-reconnecting\|🚀 Attempting auto-reconnection" "$ANDROID_LOG" 2>/dev/null; then
                echo "✅ Auto-reconnection system activated successfully"
                echo "$(date): Auto-reconnection system activated" >> "$MAIN_LOG"
            else
                echo "❌ Auto-reconnection system did not activate"
                echo "$(date): Auto-reconnection system failed to activate" >> "$MAIN_LOG"
            fi
        fi
    fi
    
    if [ $((ELAPSED_SINCE_UNLOCK % 30)) -eq 0 ]; then
        echo "⏳ Unlock +${ELAPSED_SINCE_UNLOCK}s - Monitoring..."
    fi
    
    sleep 5
done

echo ""
echo "📊 TEST RESULTS ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Calculate final battery usage
FINAL_BATTERY=$(adb shell dumpsys battery | grep level | cut -d: -f2 | tr -d ' ')
TOTAL_BATTERY_USED=$((BATTERY_LEVEL - FINAL_BATTERY))
ACTUAL_MINUTES=$((($(date +%s) - START_TIME) / 60))
BATTERY_RATE=$(echo "scale=2; $TOTAL_BATTERY_USED / $ACTUAL_MINUTES * 60" | bc -l 2>/dev/null || echo "N/A")

{
    echo ""
    echo "FINAL TEST RESULTS"
    echo "Test completed: $(date)"
    echo "Actual duration: $ACTUAL_MINUTES minutes"
    echo "Battery usage: $TOTAL_BATTERY_USED% (${BATTERY_RATE}%/hour)"
    echo "Unlock test performed at: minute $UNLOCK_MINUTE"
    echo "Disconnect detected after unlock: $DISCONNECT_DETECTED"
} >> "$MAIN_LOG"

echo "🔋 Battery Performance:"
echo "   Started: ${BATTERY_LEVEL}%"
echo "   Ended: ${FINAL_BATTERY}%"  
echo "   Used: ${TOTAL_BATTERY_USED}% over $ACTUAL_MINUTES minutes"
echo "   Rate: ${BATTERY_RATE}%/hour"

echo ""
echo "🎯 Unlock Test Results:"
if [ "$DISCONNECT_DETECTED" = true ]; then
    if grep -q "Auto-reconnecting" "$ANDROID_LOG" 2>/dev/null; then
        echo "   ✅ PASS: Disconnect detected and auto-reconnection activated"
        TEST_RESULT="PASS"
    else
        echo "   ⚠️  PARTIAL: Disconnect detected but auto-reconnection failed"
        TEST_RESULT="PARTIAL"
    fi
else
    echo "   ❓ UNCLEAR: No disconnect detected (may indicate fix worked or test issue)"
    TEST_RESULT="UNCLEAR"
fi

echo ""
echo "📁 Generated Test Artifacts:"
echo "   Main log: $MAIN_LOG"
echo "   Android logs: $ANDROID_LOG"
echo "   Battery log: $BATTERY_LOG"

echo ""
echo "🏁 COMPREHENSIVE FIELD TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Result: $TEST_RESULT"
echo "Duration: $ACTUAL_MINUTES minutes"
echo "Battery efficiency: ${BATTERY_RATE}%/hour"
echo "Unlock test: $UNLOCK_MINUTE minutes"
echo ""

case "$TEST_RESULT" in
    "PASS")
        echo "🎉 FIELD TEST SUCCESSFUL - Production fix validated!"
        exit 0
        ;;
    "PARTIAL") 
        echo "⚠️  FIELD TEST PARTIAL - Disconnect detection works, reconnection needs review"
        exit 1
        ;;
    "UNCLEAR")
        echo "❓ FIELD TEST UNCLEAR - Manual review of logs required"
        exit 2
        ;;
esac