# SRT Failover Testing Guide

## 🎯 Objective

Test the automatic SRT failover system by simulating RTMP failure and verifying:

1. Automatic failover to SRT backup after 3 consecutive failures
2. Automatic recovery to RTMP after 5 consecutive healthy checks
3. Performance metrics during failover/recovery

## 📋 Prerequisites

- [x] SRT 1.5.4 installed
- [x] NGINX RTMP server running (ports 1935, 8080)
- [x] Both YouTube channels streaming
- [x] SRT_BACKUP_URL configured in .env: `srt://localhost:9000?mode=caller`

## 🔧 Test Setup

### Step 1: Start SRT Backup Receiver

In Terminal 1, start the SRT receiver:

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
./test_srt_receiver.sh 9000

```

You should see:

```text
=============================================
SRT Backup Receiver Test
=============================================
Listening on port: 9000
...

```

**Keep this terminal open** - it will receive the backup stream when failover occurs.

### Step 2: Start Streaming Application

In Terminal 2, start the streaming application with monitoring:

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
./venv/bin/python src/main_hybrid.py --no-api 2>&1 | tee failover_test_log.txt

```

Or start it normally and monitor the logs.

### Step 3: Verify Initial State

Check that streaming is active:

- Both YouTube channels should be streaming via NGINX
- Health monitoring should show "RTMP" mode
- Look for logs like: `Health Summary: 2/2 destinations streaming [RTMP]`

## 🧪 Test Scenarios

### Test 1: Simulate RTMP Failure (Automatic Failover)

**Objective**: Verify automatic switch to SRT backup after RTMP failure.

**Steps**:

1. **Check current status** (while streaming):
   - RTMP mode should be active
   - Both YouTube channels streaming

2. **Simulate RTMP failure** by stopping NGINX:

   ```bash
   # Terminal 3
   sudo nginx -s stop

   ```

3. **Monitor the logs** for failover sequence:
   - Every 5 seconds, you'll see health checks
   - After ~15 seconds (3 failures × 5 sec), look for:

```text
     RTMP unhealthy (failure count: 1/3)
     RTMP unhealthy (failure count: 2/3)
     RTMP unhealthy (failure count: 3/3)
     ⚠️ RTMP failure threshold reached - initiating failover to SRT backup
     🔄 FAILOVER: Switching to SRT backup 'SRT Backup'
     ✅ Successfully failed over to SRT backup at srt://localhost:9000?mode=caller

     ```

4. **Check SRT receiver terminal** (Terminal 1):
   - Should start receiving stream data
   - You'll see connection established and data flowing

5. **Verify failover state**:
   - Health logs should now show: `[SRT BACKUP]`
   - SRT destination status: STREAMING
   - RTMP destination status: FAILED

**Expected Timeline**:
- T+0s: Stop NGINX
- T+5s: First failure detected (count: 1/3)
- T+10s: Second failure detected (count: 2/3)
- T+15s: Third failure detected → **FAILOVER TRIGGERED**
- T+16s: SRT backup streaming

### Test 2: Automatic Recovery to RTMP

**Objective**: Verify automatic switch back to RTMP when it recovers.

**Steps**:

1. **Verify SRT backup is active**:
   - Logs show `[SRT BACKUP]`
   - SRT receiver is receiving data

2. **Restore RTMP** by restarting NGINX:

   ```bash
   # Terminal 3
   sudo nginx

   ```

1. **Verify NGINX is running**:

   ```bash
   sudo netstat -an | grep LISTEN | grep -E "1935|8080"

   ```

   Should show both ports listening.

2. **Monitor the logs** for recovery sequence:
   - Every 5 seconds, health checks run
   - After ~25 seconds (5 recoveries × 5 sec), look for:

```text
     RTMP recovery detected (recovery count: 1/5)
     RTMP recovery detected (recovery count: 2/5)
     RTMP recovery detected (recovery count: 3/5)
     RTMP recovery detected (recovery count: 4/5)
     RTMP recovery detected (recovery count: 5/5)
     ✅ RTMP recovery threshold reached - switching back to RTMP
     🔄 RECOVERY: Switching back to RTMP destinations
     ✅ Successfully recovered to RTMP streaming

     ```

5. **Verify recovery state**:
   - Health logs should now show: `[RTMP]`
   - RTMP destination status: STREAMING
   - SRT destination status: DISCONNECTED
   - Both YouTube channels streaming again

**Expected Timeline**:
- T+0s: Restart NGINX
- T+5s: First recovery detected (count: 1/5)
- T+10s: Second recovery detected (count: 2/5)
- T+15s: Third recovery detected (count: 3/5)
- T+20s: Fourth recovery detected (count: 4/5)
- T+25s: Fifth recovery detected → **RECOVERY TRIGGERED**
- T+26s: RTMP streaming restored

### Test 3: Verify State Persistence

**Objective**: Verify failover state is tracked correctly.

**Steps**:

1. Query failover status (if API is running):

   ```bash
   curl http://localhost:8000/api/egress/failover-status | jq

   ```

   Expected response:

   ```json
   {
     "using_srt_backup": false,
     "rtmp_failure_count": 0,
     "rtmp_recovery_count": 0,
     "last_failover_time": "2025-11-03T14:30:45.123456",
     "last_recovery_time": "2025-11-03T14:31:15.654321",
     "thresholds": {
       "failure_threshold": 3,
       "recovery_threshold": 5,
       "drop_rate_threshold": 10.0,
       "zero_bitrate_threshold": 30
     }
   }

   ```

1. Verify timestamps are recorded for both events

## 📊 Performance Metrics to Document

During testing, document these metrics:

### Failover Metrics

- **Time to detect failure**: ~15 seconds (3 × 5 sec)
- **Failover transition time**: < 2 seconds
- **Total downtime**: ~16-17 seconds
- **SRT connection latency**: Check receiver logs
- **SRT bitrate during backup**: Monitor receiver stats

### Recovery Metrics

- **Time to detect recovery**: ~25 seconds (5 × 5 sec)
- **Recovery transition time**: < 2 seconds
- **Total recovery time**: ~26-27 seconds

### Stream Quality

- **Drop rate before failover**: Should be 0% (connection lost)
- **Drop rate during SRT backup**: Monitor for stability
- **Drop rate after recovery**: Should return to normal

## 🔍 Monitoring Commands

### Check NGINX status

```bash

# Check if NGINX is running

ps aux | grep nginx | grep -v grep

# Check NGINX ports

sudo netstat -an | grep LISTEN | grep -E "1935|8080"

# Check NGINX stats

curl -s http://localhost:8080/stat

```

### Check SRT receiver

```bash

# In Terminal 1, watch for connection messages
# Look for: "Connection established"
# Monitor data transfer rate

```text

### Check application logs

```bash

# Follow the log file

tail -f failover_test_log.txt

# Search for failover events

grep -i "failover\|recovery" failover_test_log.txt

# Count health checks

grep "Health Summary" failover_test_log.txt | wc -l

```

## ✅ Success Criteria

- [ ] SRT receiver successfully receives backup stream after failover
- [ ] Failover triggers after exactly 3 consecutive failures (~15 sec)
- [ ] Recovery triggers after exactly 5 consecutive healthy checks (~25 sec)
- [ ] No errors during failover/recovery transitions
- [ ] Stream quality maintained during SRT backup
- [ ] YouTube channels resume streaming after recovery
- [ ] Failover timestamps recorded correctly

## 🐛 Troubleshooting

### SRT receiver doesn't receive stream

- Check firewall: `sudo pfctl -s rules | grep 9000`
- Verify port is listening: `lsof -i :9000`
- Check SRT URL in .env matches receiver port

### Failover doesn't trigger

- Check RTMP actually failed (NGINX stopped)
- Verify health monitoring is running (look for "Health monitoring started")
- Check thresholds in logs

### Recovery doesn't trigger

- Verify NGINX actually started: `ps aux | grep nginx`
- Check ports are listening: `netstat -an | grep 1935`
- Wait full 25 seconds for 5 health checks

### Stream quality issues

- Monitor drop rates in logs
- Check network bandwidth
- Verify OBS encoding settings

## 📝 Test Results Template

```text

## SRT Failover Test Results - [Date]

### Test Environment

- OBS Version: [version]
- NGINX Version: 1.27.0
- SRT Version: 1.5.4
- Python Version: 3.13.7

### Test 1: RTMP Failure → SRT Failover

- Failure detection time: [X] seconds
- Failover transition time: [X] seconds
- SRT connection established: ✅ / ❌
- Stream received by SRT backup: ✅ / ❌
- Notes: [observations]

### Test 2: RTMP Recovery

- Recovery detection time: [X] seconds
- Recovery transition time: [X] seconds
- RTMP streaming restored: ✅ / ❌
- YouTube channels active: ✅ / ❌
- Notes: [observations]

### Performance Metrics

- SRT latency: [X] ms
- SRT bitrate: [X] Mbps
- Drop rate during backup: [X]%
- Total test duration: [X] minutes

### Issues Encountered

- [List any problems]

### Recommendations

- [Any improvements or observations]

```

## 🎬 Quick Test Script

For automated testing, here's a quick script:

```bash

#!/bin/bash

echo "Starting automated failover test..."
echo ""

echo "Step 1: Stopping NGINX to trigger failover..."
sudo nginx -s stop
echo "Waiting 20 seconds for failover..."
sleep 20

echo ""
echo "Step 2: Restarting NGINX to trigger recovery..."
sudo nginx
echo "Waiting 30 seconds for recovery..."
sleep 30

echo ""
echo "Test complete! Check logs for failover/recovery events."
echo "Look for: 🔄 FAILOVER and ✅ Successfully recovered"

```text

## 🚀 Next Steps After Testing

1. Document actual failover/recovery times
2. Tune thresholds if needed (currently 3/5)
3. Test with different failure scenarios (high drop rate, intermittent issues)
4. Consider alerting/monitoring integration
5. Update production runbook with failover procedures

