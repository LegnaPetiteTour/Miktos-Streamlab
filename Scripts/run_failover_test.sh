#!/bin/bash
#
# Automated SRT Failover Test
# Tests automatic failover and recovery
#

set -e

echo "============================================="
echo "Automated SRT Failover Test"
echo "============================================="
echo ""
echo "This script will:"
echo "  1. Stop NGINX to trigger SRT failover (~15 sec)"
echo "  2. Wait for failover to complete"
echo "  3. Restart NGINX to trigger recovery (~25 sec)"
echo "  4. Wait for recovery to complete"
echo ""
echo "Make sure:"
echo "  - SRT receiver is running (./test_srt_receiver.sh)"
echo "  - Application is streaming"
echo ""
read -p "Press Enter to start test (Ctrl+C to cancel)..."
echo ""

# Test 1: Trigger failover
echo "============================================="
echo "TEST 1: Triggering Failover"
echo "============================================="
echo "Stopping NGINX..."
sudo nginx -s stop 2>/dev/null || echo "NGINX already stopped"

echo ""
echo "Waiting 20 seconds for failover detection..."
echo "(Should trigger after ~15 seconds)"
for i in {20..1}; do
    echo -ne "\rTime remaining: $i seconds "
    sleep 1
done
echo -e "\n"

echo "Failover should now be complete!"
echo "Check application logs for: '🔄 FAILOVER'"
echo ""
read -p "Press Enter to continue to recovery test..."
echo ""

# Test 2: Trigger recovery
echo "============================================="
echo "TEST 2: Triggering Recovery"
echo "============================================="
echo "Starting NGINX..."
sudo nginx

# Verify NGINX started
sleep 2
if pgrep nginx > /dev/null; then
    echo "✅ NGINX is running"
    sudo netstat -an | grep LISTEN | grep -E "1935|8080"
else
    echo "❌ NGINX failed to start!"
    exit 1
fi

echo ""
echo "Waiting 30 seconds for recovery detection..."
echo "(Should trigger after ~25 seconds)"
for i in {30..1}; do
    echo -ne "\rTime remaining: $i seconds "
    sleep 1
done
echo -e "\n"

echo "============================================="
echo "Test Complete!"
echo "============================================="
echo ""
echo "Recovery should now be complete!"
echo "Check application logs for: '✅ Successfully recovered'"
echo ""
echo "Review the logs for failover/recovery events:"
echo "  grep -i 'failover\\|recovery' failover_test_log.txt"
echo ""
echo "Expected sequence:"
echo "  1. RTMP unhealthy (3 times)"
echo "  2. 🔄 FAILOVER: Switching to SRT backup"
echo "  3. RTMP recovery detected (5 times)"
echo "  4. 🔄 RECOVERY: Switching back to RTMP"
echo ""
