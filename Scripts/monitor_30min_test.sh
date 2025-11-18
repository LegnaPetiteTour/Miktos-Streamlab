#!/bin/bash

# 30-Minute Studio Mode Battery & Thermal Test Monitor
# This script captures battery and thermal data every minute via ADB
# Use this during initial setup, then UNPLUG phone for accurate battery test

TEST_DURATION_MINUTES=30
OUTPUT_FILE="/Users/atorrella/Desktop/Miktos Streamlab/test_results_$(date +%Y%m%d_%H%M%S).csv"

echo "=== 30-Minute Studio Mode Test Monitor ==="
echo "Duration: ${TEST_DURATION_MINUTES} minutes"
echo "Output: ${OUTPUT_FILE}"
echo ""
echo "📱 SETUP INSTRUCTIONS:"
echo "1. Start desktop receiver: python3 tcp_h264_receiver_with_preview.py 8554"
echo "2. Start streaming on phone to 192.168.2.36:8554"
echo "3. Enter Studio Mode on phone"
echo "4. Press ENTER to start monitoring..."
read -r

echo "⚠️  IMPORTANT: After you see the first data capture below,"
echo "   UNPLUG the USB cable to get accurate battery readings!"
echo ""
echo "Starting data collection in 5 seconds..."
sleep 5

# Create CSV header
echo "Timestamp,Elapsed_Min,Battery_Level,Battery_Temp_C,Thermal_Status,Stream_Status,Notes" > "$OUTPUT_FILE"

START_TIME=$(date +%s)

echo ""
echo "🔍 Monitoring started at $(date '+%H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for i in $(seq 0 $TEST_DURATION_MINUTES); do
    CURRENT_TIME=$(date +%s)
    ELAPSED_MIN=$(( (CURRENT_TIME - START_TIME) / 60 ))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Get battery level (percentage)
    BATTERY_LEVEL=$(adb shell dumpsys battery | grep 'level:' | awk '{print $2}')
    
    # Get battery temperature (convert from tenths of degrees C)
    BATTERY_TEMP_RAW=$(adb shell dumpsys battery | grep 'temperature:' | awk '{print $2}')
    BATTERY_TEMP=$(echo "scale=1; $BATTERY_TEMP_RAW / 10" | bc)
    
    # Check if streaming (look for CameraStreamerService in running services)
    STREAM_CHECK=$(adb shell dumpsys activity services | grep -c "CameraStreamerService")
    if [ "$STREAM_CHECK" -gt 0 ]; then
        STREAM_STATUS="ACTIVE"
    else
        STREAM_STATUS="STOPPED"
    fi
    
    # Thermal status (would need logcat for actual thermal state, simplified here)
    THERMAL_STATUS="OK"
    if (( $(echo "$BATTERY_TEMP >= 38" | bc -l) )); then
        THERMAL_STATUS="WARM"
    fi
    if (( $(echo "$BATTERY_TEMP >= 42" | bc -l) )); then
        THERMAL_STATUS="HOT"
    fi
    
    # Special notes
    NOTES=""
    if [ $i -eq 0 ]; then
        NOTES="START - Unplug USB cable now!"
    elif [ $i -eq $TEST_DURATION_MINUTES ]; then
        NOTES="END"
    fi
    
    # Write to CSV
    echo "$TIMESTAMP,$ELAPSED_MIN,$BATTERY_LEVEL,$BATTERY_TEMP,$THERMAL_STATUS,$STREAM_STATUS,$NOTES" >> "$OUTPUT_FILE"
    
    # Display to console
    printf "[%02d min] Battery: %3d%% | Temp: %4.1f°C | Thermal: %-8s | Stream: %s\n" \
        $ELAPSED_MIN "$BATTERY_LEVEL" "$BATTERY_TEMP" "$THERMAL_STATUS" "$STREAM_STATUS"
    
    # Special warnings
    if [ $i -eq 0 ]; then
        echo "⚠️  >>> UNPLUG USB CABLE NOW FOR ACCURATE BATTERY TEST! <<<"
        echo ""
    fi
    
    if [ "$STREAM_STATUS" != "ACTIVE" ]; then
        echo "⚠️  WARNING: Stream not detected!"
    fi
    
    # Wait 60 seconds before next reading (except last iteration)
    if [ $i -lt $TEST_DURATION_MINUTES ]; then
        sleep 60
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Test complete! Results saved to:"
echo "   $OUTPUT_FILE"
echo ""

# Calculate battery drain
INITIAL_BATTERY=$(head -2 "$OUTPUT_FILE" | tail -1 | cut -d',' -f3)
FINAL_BATTERY=$(tail -1 "$OUTPUT_FILE" | cut -d',' -f3)
BATTERY_DRAIN=$((INITIAL_BATTERY - FINAL_BATTERY))
DRAIN_RATE=$(echo "scale=2; $BATTERY_DRAIN / $TEST_DURATION_MINUTES" | bc)

echo "📊 TEST SUMMARY:"
echo "   Duration: ${TEST_DURATION_MINUTES} minutes"
echo "   Initial Battery: ${INITIAL_BATTERY}%"
echo "   Final Battery: ${FINAL_BATTERY}%"
echo "   Total Drain: ${BATTERY_DRAIN}%"
echo "   Drain Rate: ${DRAIN_RATE}% per minute"
echo ""

# Check against target (2% per minute = 60% in 30 min)
TARGET_DRAIN=$((TEST_DURATION_MINUTES * 2))
if [ "$BATTERY_DRAIN" -le "$TARGET_DRAIN" ]; then
    echo "✅ PASS: Battery drain within target (<${TARGET_DRAIN}%)"
else
    echo "❌ FAIL: Battery drain exceeds target (>${TARGET_DRAIN}%)"
fi

echo ""
echo "Next: Review data and proceed with Test 2 (Remote Control)"
