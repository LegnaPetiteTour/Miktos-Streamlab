#!/bin/bash

# Simple 30-minute test monitor - Live tracking
# Logs battery checks to file while displaying real-time status

TEST_FILE="/Users/atorrella/Desktop/Miktos Streamlab/test_30min_$(date +%Y%m%d_%H%M%S).log"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     📱 30-MINUTE STUDIO MODE BATTERY & STABILITY TEST 📱      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Test log: $TEST_FILE"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "                         INSTRUCTIONS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "ON YOUR PHONE:"
echo "  1. ✅ Open StreamLab Camera app"
echo "  2. ✅ Enter IP: 192.168.2.36"
echo "  3. ✅ Enter Port: 8554"
echo "  4. ✅ Press CONNECT button"
echo "  5. ⏳ Wait for video to appear on desktop"
echo "  6. ✅ Press BACK button if needed to see battery %"
echo "  7. 📝 Note initial battery level"
echo "  8. ✅ Press ENTER STUDIO MODE button"
echo "  9. ⚠️  UNPLUG USB CABLE from phone"
echo "  10. ✅ Press ENTER here to start 30-minute timer"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
read -p "Press ENTER when ready to start 30-minute test... "

START_TIME=$(date +%s)
START_DISPLAY=$(date '+%H:%M:%S')

echo "" | tee -a "$TEST_FILE"
echo "🎬 TEST STARTED at $START_DISPLAY" | tee -a "$TEST_FILE"
echo "═══════════════════════════════════════════════════════════════════" | tee -a "$TEST_FILE"
echo "" | tee -a "$TEST_FILE"

read -p "📝 Enter INITIAL battery %: " INITIAL_BATTERY
echo "Initial Battery: $INITIAL_BATTERY%" | tee -a "$TEST_FILE"
echo "" | tee -a "$TEST_FILE"

echo "⏱️  30-MINUTE COUNTDOWN STARTED" | tee -a "$TEST_FILE"
echo "Check battery at: 5, 10, 15, 20, 25, 30 minutes" | tee -a "$TEST_FILE"
echo "" | tee -a "$TEST_FILE"

# Function to show elapsed time
show_status() {
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))
    REMAINING=$((1800 - ELAPSED))
    REMAINING_MIN=$((REMAINING / 60))
    REMAINING_SEC=$((REMAINING % 60))
    
    printf "\r⏱️  Elapsed: %02d:%02d | Remaining: %02d:%02d " $MINUTES $SECONDS $REMAINING_MIN $REMAINING_SEC
}

# Monitor for 30 minutes (1800 seconds)
CHECKPOINTS=(300 600 900 1200 1500 1800)
CHECKPOINT_LABELS=("5 min" "10 min" "15 min" "20 min" "25 min" "30 min")
CHECKPOINT_INDEX=0

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    # Show live status
    show_status
    
    # Check if we've reached a checkpoint
    if [ $CHECKPOINT_INDEX -lt ${#CHECKPOINTS[@]} ]; then
        if [ $ELAPSED -ge ${CHECKPOINTS[$CHECKPOINT_INDEX]} ]; then
            echo "" # New line after timer
            echo "" | tee -a "$TEST_FILE"
            echo "═══════════════════════════════════════════════════════════════════" | tee -a "$TEST_FILE"
            TIMESTAMP=$(date '+%H:%M:%S')
            echo "⏰ CHECKPOINT: ${CHECKPOINT_LABELS[$CHECKPOINT_INDEX]} - $TIMESTAMP" | tee -a "$TEST_FILE"
            echo "═══════════════════════════════════════════════════════════════════" | tee -a "$TEST_FILE"
            
            read -p "📝 Enter current battery %: " BATTERY
            echo "Battery at ${CHECKPOINT_LABELS[$CHECKPOINT_INDEX]}: $BATTERY%" | tee -a "$TEST_FILE"
            
            read -p "📺 Stream still active? (y/n): " STREAM
            if [ "$STREAM" = "y" ] || [ "$STREAM" = "Y" ]; then
                echo "Stream: ACTIVE ✅" | tee -a "$TEST_FILE"
            else
                echo "Stream: DISCONNECTED ❌" | tee -a "$TEST_FILE"
            fi
            
            if [ $CHECKPOINT_INDEX -eq 2 ] || [ $CHECKPOINT_INDEX -eq 5 ]; then
                read -p "🌡️  Phone temperature (cool/warm/hot): " TEMP
                echo "Temperature: $TEMP" | tee -a "$TEST_FILE"
            fi
            
            CHECKPOINT_INDEX=$((CHECKPOINT_INDEX + 1))
            echo "" | tee -a "$TEST_FILE"
            
            # If this was the last checkpoint, break
            if [ $CHECKPOINT_INDEX -ge ${#CHECKPOINTS[@]} ]; then
                break
            fi
        fi
    fi
    
    sleep 1
done

echo "" | tee -a "$TEST_FILE"
echo "═══════════════════════════════════════════════════════════════════" | tee -a "$TEST_FILE"
echo "🏁 TEST COMPLETED at $(date '+%H:%M:%S')" | tee -a "$TEST_FILE"
echo "═══════════════════════════════════════════════════════════════════" | tee -a "$TEST_FILE"
echo "" | tee -a "$TEST_FILE"

read -p "📝 Enter FINAL battery %: " FINAL_BATTERY
echo "Final Battery: $FINAL_BATTERY%" | tee -a "$TEST_FILE"
echo "" | tee -a "$TEST_FILE"

# Calculate results
DRAIN=$((INITIAL_BATTERY - FINAL_BATTERY))
DRAIN_RATE=$(echo "scale=2; $DRAIN / 30" | bc 2>/dev/null || echo "N/A")

echo "📊 RESULTS SUMMARY" | tee -a "$TEST_FILE"
echo "═══════════════════════════════════════════════════════════════════" | tee -a "$TEST_FILE"
echo "Initial Battery: $INITIAL_BATTERY%" | tee -a "$TEST_FILE"
echo "Final Battery:   $FINAL_BATTERY%" | tee -a "$TEST_FILE"
echo "Total Drain:     $DRAIN%" | tee -a "$TEST_FILE"
echo "Drain Rate:      ${DRAIN_RATE}% per minute" | tee -a "$TEST_FILE"
echo "" | tee -a "$TEST_FILE"

# Check pass/fail
if [ $DRAIN -le 60 ]; then
    echo "✅ PASS: Battery drain within target (≤60%)" | tee -a "$TEST_FILE"
else
    echo "❌ FAIL: Battery drain exceeds target (>60%)" | tee -a "$TEST_FILE"
fi
echo "" | tee -a "$TEST_FILE"

echo "Full log saved to: $TEST_FILE"
echo ""
echo "Press ENTER to exit..."
read
