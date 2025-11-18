# 4-Layer Monitoring System - Testing Guide

## What Was Implemented

A complete 4-layer monitoring system to fix the disconnect detection issues, especially the "phone locked for 60+ minutes" bug.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CameraStreamer.kt                         │
│                   (State Machine)                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: SocketHealthMonitor                               │
│  - Active socket probing every 2 seconds                     │
│  - Writes test byte (0x00) to force OS to check connection │
│  - Detects dead sockets immediately                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: DataFlowMonitor                                   │
│  - Tracks confirmed successful writes                       │
│  - 10-second timeout if no data flows                       │
│  - Detects encoder running but socket failing               │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: ScreenStateMonitor                                │
│  - Detects screen lock/unlock events                        │
│  - Immediately verifies connection on unlock                │
│  - Triggers reconnection if dead                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: NetworkStateMonitor (existing)                    │
│  - WiFi/LTE network changes                                 │
│  - Triggers immediate reconnection when WiFi returns        │
└─────────────────────────────────────────────────────────────┘
```

### State Machine

```
Stopped → Starting → Running ⇄ Disconnected ⇄ Reconnecting → Error
                                                  ↓
                                              Stopping → Stopped
```

## Files Created

1. **StreamingState.kt** - State definitions
   - `StreamingState` sealed class (Stopped, Starting, Running, Disconnected, Reconnecting, Error, Stopping)
   - `ConnectionInfo` data class
   - `NetworkType` enum
   - `ErrorType` enum

2. **SocketHealthMonitor.kt** - Active socket probing (THE CRITICAL FIX!)
   - Checks every 2 seconds
   - Writes test byte to force OS to verify connection
   - Immediately detects dead sockets

3. **DataFlowMonitor.kt** - Data flow verification
   - Tracks confirmed successful writes
   - 10-second timeout detection
   - Catches encoder running but socket dead

4. **ScreenStateMonitor.kt** - Lock/unlock detection
   - Listens for ACTION_SCREEN_OFF and ACTION_USER_PRESENT
   - Triggers post-unlock verification
   - Critical for 60+ minute lock bug

5. **CameraStreamer.kt** - Integration
   - Added `verifyConnectionAfterUnlock()` function
   - State machine integration
   - Monitor lifecycle management

## Testing Protocol

### Test 1: Quick Lock/Unlock (15 minutes) ⚠️ RUN THIS FIRST

**Purpose:** Verify basic disconnect detection and post-unlock verification

**Steps:**
1. Start receiver on desktop:
   ```bash
   cd "/Users/atorrella/Desktop/Miktos Streamlab"
   source .venv/bin/activate
   python tcp_h264_receiver_with_preview.py
   ```

2. Open app on phone, start streaming to `192.168.2.36:8554`

3. Let stream run for 5 minutes (verify video playing)

4. Lock phone for 2 minutes

5. Unlock phone

6. **Expected Result:**
   - Within 15 seconds, you should see either:
     - ✅ Stream continues (connection survived), OR
     - 🔄 "Reconnecting..." message → "✅ Reconnected!"
   - Desktop should show continuous data or brief reconnection gap

7. Check logs:
   ```bash
   adb logcat -d | grep -E "CameraStream|SocketHealth|DataFlow|ScreenState"
   ```
   Look for:
   - `🔓 Screen unlocked - verifying connection`
   - `✅ Post-unlock verification passed` OR
   - `❌ Post-unlock verification FAILED - triggering reconnect`

### Test 2: Forced Disconnect (Immediate Detection)

**Purpose:** Verify disconnect is detected within 4-6 seconds

**Steps:**
1. Start streaming
2. On desktop, kill receiver: `Cmd+C` or `kill -9 <pid>`
3. Watch Android app

4. **Expected Result:**
   - Within 4-6 seconds max:
     - UI shows: "🔄 Connection lost - Reconnecting... (1/5)"
     - Logs show one of:
       - `❌ Active probe failed - socket is DEAD` (SocketHealthMonitor)
       - `❌ Write error` (DataFlowMonitor)

5. Restart receiver on desktop
6. Within 15-30 seconds, should reconnect automatically
7. UI shows: "✅ Reconnected!"

### Test 3: Extended Lock (60+ Minutes) - THE BIG ONE

**Purpose:** Fix the original bug - phone locked for extended period

**Steps:**
1. Start streaming
2. Let run for 10 minutes (verify stable)
3. Lock phone
4. Wait 50-60 minutes (go do something else)
5. Unlock phone

6. **Expected Result:**
   - Immediately on unlock:
     - Log: `🔓 Screen unlocked - verifying connection`
     - One of two outcomes:
       - ✅ Stream continues (connection still alive)
       - 🔄 Automatic reconnection within 15 seconds

7. Check logs for the sequence:
   ```bash
   adb logcat -d | grep -E "Screen unlocked|Post-unlock|Reconnect"
   ```

### Test 4: Network Change (WiFi → LTE → WiFi)

**Purpose:** Verify LTE failover with network monitoring

**Steps:**
1. Enable LTE failover toggle in app
2. Start streaming on WiFi
3. Turn off WiFi (forces switch to LTE or offline)
4. **Expected:** App attempts reconnection
5. Turn WiFi back on
6. **Expected:** Immediate reconnection when WiFi returns

## What to Look For in Logs

### Healthy Streaming:
```
✅ Streaming started - all 4 monitors active
✅ Socket health monitoring started (2s interval)
✅ Data flow monitoring started (10s timeout)
✅ Screen state monitoring started
✓ Data flowing - last write 0s ago
```

### Screen Unlock (Connection Alive):
```
📵 Screen locked - monitoring closely
🔓 Screen unlocked - verifying connection
✅ Post-unlock verification passed - connection is alive
```

### Screen Unlock (Connection Dead):
```
🔓 Screen unlocked - verifying connection
❌ Post-unlock verification FAILED - socket write error
🔄 Auto-reconnecting in 2s... (attempt 1/5)
```

### Disconnect Detection:
```
❌ Active probe failed - socket is DEAD: Connection reset
Socket monitor detected disconnect: Socket health check failed
🔄 Auto-reconnecting in 2s... (attempt 1/5)
```

### Successful Reconnection:
```
✅ Reconnection successful after 2 attempts!
✅ Streaming started - all 4 monitors active
```

## Why This Will Work

### Previous Implementation Problems:
1. ❌ `socket.isConnected` can lie - reports true when connection is dead
2. ❌ Write timeout detection had timing issues
3. ❌ No verification after unlock - missed dead connections
4. ❌ UI state desync - showed "streaming" when encoder was dead

### New Implementation Solutions:
1. ✅ **Active Socket Probing** - Actually writes to force OS to check
2. ✅ **Dedicated Data Flow Monitor** - Tracks confirmed writes, not just encoder state
3. ✅ **Post-Unlock Verification** - Immediately checks when phone unlocks
4. ✅ **State Machine** - Proper state tracking prevents desync
5. ✅ **Multi-Layer** - If one layer misses, another will catch it

## Monitoring Coverage

| Scenario | Detection Layer | Detection Time |
|----------|----------------|----------------|
| Socket dies immediately | SocketHealthMonitor | 2-4 seconds |
| Encoder runs, socket fails | DataFlowMonitor | 10 seconds max |
| Connection dies during lock | ScreenStateMonitor | Immediate on unlock |
| Network change (WiFi lost) | NetworkStateMonitor | Immediate |
| Write failures | DataFlowMonitor | 3 consecutive failures |

## Next Steps

1. ✅ Build and install complete (DONE)
2. ⏳ Run Test 1 (15-minute lock/unlock)
3. ⏳ Run Test 2 (forced disconnect)
4. ⏳ Run Test 3 (60+ minute lock) - THE CRITICAL TEST
5. ⏳ Document results
6. ⏳ If all pass, commit and deploy

## Troubleshooting

### If disconnect still not detected:
1. Check logs for monitor initialization:
   ```bash
   adb logcat -d | grep "monitoring started"
   ```
   Should see all 4 monitors start.

2. Check if monitors are running:
   ```bash
   adb logcat -d | grep -E "Socket health|Data flowing"
   ```

3. Verify post-unlock trigger:
   ```bash
   adb logcat -d | grep "Screen unlocked"
   ```

### If reconnection fails:
1. Check network callback:
   ```bash
   adb logcat -d | grep "Network callback"
   ```

2. Check stored connection parameters:
   ```bash
   adb logcat -d | grep "Connection parameters stored"
   ```

3. Check reconnection attempts:
   ```bash
   adb logcat -d | grep "Auto-reconnecting"
   ```

## Success Criteria

✅ **Test 1 passes** - Basic lock/unlock works  
✅ **Test 2 passes** - Disconnect detected within 6 seconds  
✅ **Test 3 passes** - 60+ minute lock reconnects on unlock  

If all three pass, the bug is FIXED! 🎉

---

**Date Implemented:** November 17, 2025  
**Commit:** Ready for testing  
**Status:** ✅ Built and installed, ready for field test
