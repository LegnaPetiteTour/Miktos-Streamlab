# 🎯 SRT Failover Test - Quick Start

## ✅ All Prerequisites Met

Your system is ready for SRT failover testing:

- ✅ SRT 1.5.4 installed
- ✅ NGINX running (ports 1935, 8080)
- ✅ SRT_BACKUP_URL configured: `srt://localhost:9000?mode=caller`
- ✅ YouTube channels configured
- ✅ Test scripts ready

## 🚀 Three-Terminal Quick Test (5 minutes)

### Terminal 1: Start SRT Receiver

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
./test_srt_receiver.sh 9000

```

**Keep this running** - it will receive the backup stream

### Terminal 2: Start Streaming Application

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
./venv/bin/python src/main_hybrid.py --no-api 2>&1 | tee failover_test_log.txt

```text
Wait for: `Health monitoring started (5-second interval)`

### Terminal 3: Run Automated Test

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
./run_failover_test.sh

```bash

## 📊 What to Watch For

### In Terminal 2 (Application Logs)

**During Failover (~15 seconds after NGINX stops):**

```text
RTMP unhealthy (failure count: 1/3)
RTMP unhealthy (failure count: 2/3)
RTMP unhealthy (failure count: 3/3)
⚠️ RTMP failure threshold reached
🔄 FAILOVER: Switching to SRT backup 'SRT Backup'
✅ Successfully failed over to SRT backup
Health Summary: 1/1 destinations streaming [SRT BACKUP]

**During Recovery (~25 seconds after NGINX restarts):**

```text
RTMP recovery detected (recovery count: 1/5)
...
RTMP recovery detected (recovery count: 5/5)
✅ RTMP recovery threshold reached
🔄 RECOVERY: Switching back to RTMP destinations
✅ Successfully recovered to RTMP streaming
Health Summary: 2/2 destinations streaming [RTMP]
```

```text
### In Terminal 1 (SRT Receiver)

Connection established
Receiving data...
```

## ⏱️ Expected Timeline

| Event | Time | What Happens |
|-------|------|--------------|
| T+0s | Start | NGINX stopped |
| T+5s | +5s | First failure detected |
| T+10s | +10s | Second failure detected |
| T+15s | +15s | **FAILOVER TO SRT** |
| T+16s | +16s | SRT streaming active |
| T+20s | +20s | NGINX restarted |
| T+25s | +25s | First recovery detected |
| T+45s | +45s | **RECOVERY TO RTMP** |
| T+46s | +46s | RTMP streaming restored |

### Total test time: ~50 seconds

## 🔍 Quick Verification Commands

```bash

# Check NGINX status

ps aux | grep nginx | grep -v grep

# Check NGINX ports

sudo netstat -an | grep LISTEN | grep -E "1935|8080"

# Check logs for failover events

grep -i "failover\|recovery" failover_test_log.txt

# Count health checks

grep "Health Summary" failover_test_log.txt | tail -5

```text

## 📝 Success Checklist

- [ ] SRT receiver connects when failover triggers
- [ ] Failover happens after ~15 seconds
- [ ] Logs show "🔄 FAILOVER" message
- [ ] Logs show "[SRT BACKUP]" in health summary
- [ ] Recovery happens after ~25 seconds
- [ ] Logs show "✅ Successfully recovered"
- [ ] Logs show "[RTMP]" in health summary after recovery
- [ ] No errors during transitions

## 🐛 Quick Troubleshooting

**SRT receiver doesn't connect:**
- Check port: `lsof -i :9000`
- Verify URL in .env matches: `srt://localhost:9000?mode=caller`

**Failover doesn't trigger:**
- Verify NGINX stopped: `ps aux | grep nginx`
- Check health monitoring is running in logs
- Wait full 15 seconds (3 × 5 sec checks)

**Recovery doesn't trigger:**
- Verify NGINX started: `ps aux | grep nginx`
- Check ports listening: `netstat -an | grep 1935`
- Wait full 25 seconds (5 × 5 sec checks)

## 📖 Full Documentation

See `SRT_FAILOVER_TEST_GUIDE.md` for:

- Detailed step-by-step instructions
- Manual testing procedures
- Performance metrics to document
- Test results template
- Advanced troubleshooting

## 🎬 Ready to Test!

Just run these three commands in three separate terminals:

```bash

# Terminal 1

./test_srt_receiver.sh 9000

# Terminal 2

./venv/bin/python src/main_hybrid.py --no-api 2>&1 | tee failover_test_log.txt

# Terminal 3

./run_failover_test.sh

```text

Good luck! 🚀

