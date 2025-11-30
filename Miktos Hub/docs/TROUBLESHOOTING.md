# Troubleshooting Guide

Common issues and solutions for Miktos Hub.

## Table of Contents

- [Server Issues](#server-issues)
- [OBS Connection](#obs-connection)
- [Camera Issues](#camera-issues)
- [Camera Discovery](#camera-discovery)
- [Database Problems](#database-problems)
- [Performance Issues](#performance-issues)
- [API Errors](#api-errors)

---

## Server Issues

### Server Won't Start

**Symptoms:**

- Server exits immediately
- Error: "Address already in use"

**Solutions:**

```bash

# Check if port is in use
lsof -ti:8000

# Kill process using port
lsof -ti:8000 | xargs kill -9

# Or use different port
python main.py --port 8001

```

### Import Errors

**Symptoms:**

- `ModuleNotFoundError`
- `No module named 'xyz'`

**Solutions:**

```bash

# Verify virtual environment
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.11+

```

### Server Crashes on Startup

**Symptoms:**

- Server starts then immediately crashes
- Database errors in logs

**Solutions:**

```bash

# Check logs
tail -f /tmp/miktos.log

# Reset database (WARNING: deletes data)
rm -rf data/miktos_hub.db
python main.py

# Verify file permissions
ls -la data/
chmod 755 data/

```

---

## OBS Connection

### OBS Won't Connect

**Symptoms:**

- `OBS Studio not connected` error
- Status shows `connected: false`

**Solutions:**

1. **Verify OBS is Running**

   ```bash
   # macOS
   ps aux | grep OBS
   
   # Windows
   tasklist | findstr obs
   ```

2. **Check WebSocket Settings**

   - Open OBS → Tools → WebSocket Server Settings
   - Ensure "Enable WebSocket server" is checked
   - Note the port (default: 4455)
   - Note the password

3. **Update Configuration**

   ```python
   # config/settings.py
   obs:
       host: "localhost"
       port: 4455  # Match OBS setting
       password: "your-actual-password"
   ```

4. **Test Connection**

   ```bash
   curl http://localhost:8000/api/obs/status
   ```

### OBS Connection Timeout

**Symptoms:**

- Long delay before connection
- Timeout errors in logs

**Solutions:**

```python

# Increase timeout in config
obs:
    connection_timeout: 10  # seconds
    retry_attempts: 3

```

### OBS Disconnects Randomly

**Symptoms:**

- Connection drops during use
- Reconnection loops in logs

**Solutions:**

1. **Check OBS CPU usage** - High load can cause disconnects
2. **Verify network stability** - WiFi issues affect localhost too
3. **Update OBS WebSocket plugin** - Ensure latest version
4. **Check OBS logs** - Look for errors in OBS log files

---

## Camera Issues

### Camera Not Detected by Imaging Edge

**Symptoms:**

- Imaging Edge Webcam doesn't show camera
- Camera not appearing in OBS device list

**Solutions:**

1. **Check USB Connection**

   ```bash
   # macOS - Check connected USB devices
   system_profiler SPUSBDataType | grep -i camera
   
   # Should see your camera model
   ```

2. **Verify Camera Settings**

   - Menu → Network → PC Remote Function: **On**
   - Menu → Network → PC Remote → USB Connection Mode: **PC Remote**
   - Camera display should show "PC Remote" indicator

3. **Restart Imaging Edge**

   - Quit Imaging Edge Webcam completely
   - Disconnect camera from USB
   - Restart camera
   - Reconnect USB cable
   - Launch Imaging Edge Webcam

4. **Try Different USB Port**

   - Use USB 3.0 port directly on computer (blue port)
   - Avoid USB hubs
   - Try different cable if available

5. **Check Permissions (macOS)**

   - System Settings → Privacy & Security → Camera
   - Ensure Imaging Edge Webcam is allowed

### Camera Disconnects During Stream

**Symptoms:**

- Camera feed drops mid-stream
- "Device disconnected" error in OBS
- Black screen in camera source

**Solutions:**

1. **Disable Auto Power Off**

   - Menu → Setup → Auto Power Off Temp.: **High**
   - Menu → Setup → Auto Off w/ VF: **Off**
   - Menu → Setup → Auto Power Off: **Off**

2. **Use AC Power**

   - Connect camera to AC adapter (recommended for streaming)
   - Battery drain can cause unstable connection
   - Menu → Network → USB Power Supply: **On**

3. **Check USB Cable Quality**

   - Use high-quality USB-C cable
   - Shorter cables more reliable (< 2 meters)
   - Replace worn or damaged cables
   - Avoid cheap cables from unknown brands

4. **Reduce USB Bandwidth**

   - If using multiple cameras, reduce resolution
   - Change from 4K → 1080p
   - Change from 60fps → 30fps

5. **Update Camera Firmware**

   - Check Sony support site for latest firmware
   - Newer firmware improves USB stability

### Video Lag or Stuttering

**Symptoms:**

- Choppy video in OBS preview
- Frame drops
- Laggy camera feed

**Solutions:**

1. **Reduce Camera Resolution**

   - Change Imaging Edge output: 4K → 1080p
   - Right-click OBS source → Properties → Resolution

2. **Reduce Frame Rate**

   - 60fps → 30fps reduces bandwidth by 50%

3. **Free Up Resources**

   - Close unnecessary applications
   - Close browser tabs
   - Quit other video apps

4. **Check USB Bandwidth**

   ```bash
   # macOS - Check USB usage
   system_profiler SPUSBDataType
   
   # Look for cameras on same USB controller
   # Move cameras to different controllers if possible
   ```

5. **Optimize OBS Settings**

   - Settings → Video → Downscale Filter: **Bicubic**
   - Reduce OBS canvas resolution if needed

### Poor Image Quality

**Symptoms:**

- Soft or blurry image
- Noisy/grainy video
- Washed out colors

**Solutions:**

1. **Check Camera Focus**

   - Use camera's focus magnifier
   - Enable Face/Eye AF for talking head
   - Set to Continuous AF mode
   - Clean lens (fingerprints = soft image)

2. **Adjust Camera Exposure**

   - ISO too high → grainy (keep ISO ≤ 1600 indoors)
   - Underexposed → increase ISO or open aperture
   - Overexposed → reduce ISO or close aperture

3. **Optimize Aperture**

   - Too wide (f/1.4) → soft, shallow focus
   - Too narrow (f/16) → diffraction, soft
   - **Optimal: f/2.8 - f/5.6** for most lenses

4. **Check Picture Profile**

   - Standard profile works well for streaming
   - Avoid S-Log unless color grading
   - Sharpness: 0 to +1 (avoid over-sharpening)

5. **Lighting**

   - Good lighting is crucial
   - Avoid mixed color temperatures
   - Use key light + fill light setup
   - See [OBS_SETUP.md](OBS_SETUP.md) for more

### Multi-Camera Issues

**Symptoms:**

- Only one camera works at a time
- Second camera not recognized
- Both cameras lag when used together

**Solutions:**

1. **USB Bandwidth Management**

   ```bash
   # Check USB controllers
   # macOS
   system_profiler SPUSBDataType | grep -A 10 "USB 3"
   
   # Connect each camera to different USB controller
   ```

2. **Reduce Combined Bandwidth**

   - Camera 1: 1080p @ 30fps (main)
   - Camera 2: 720p @ 30fps (secondary)
   - Avoid multiple 4K streams simultaneously

3. **Stagger Camera Connections**

   - Connect main camera first
   - Wait for it to stabilize in OBS
   - Then connect second camera

4. **Use Separate Imaging Edge Instances**

   - Some setups may need multiple instances
   - Check Imaging Edge documentation

### Audio Issues from Camera

**Symptoms:**

- No audio from camera mic
- Audio cutting out
- Echo or feedback

**Solutions:**

1. **Check Camera Audio Settings**

   - Menu → Audio Recording: **On**
   - Menu → Rec Level: **Manual** (adjust levels)
   - Wind Noise Reduction: **On** (if applicable)

2. **OBS Audio Configuration**

   - Right-click camera source → Advanced Audio Properties
   - Verify not muted
   - Check audio monitoring settings

3. **Use External Audio** (Recommended)

   - Camera mics are typically low quality
   - Use USB microphone or audio interface
   - Better quality and easier control
   - See [OBS_SETUP.md](OBS_SETUP.md) for audio setup

4. **Fix Echo/Feedback**

   - Disable audio monitoring if speakers are on
   - Use headphones
   - Check for duplicate audio sources

For detailed camera setup instructions, see [CAMERA_PAIRING.md](CAMERA_PAIRING.md).

---

## Camera Discovery

### Cameras Not Discovered

**Symptoms:**

- `GET /api/cameras/` returns empty array
- No cameras in camera list

**Solutions:**

1. **Verify Network**

   ```bash
   # Check cameras and hub on same network
   ifconfig  # macOS/Linux
   ipconfig  # Windows
   ```

2. **Check mDNS Service**

   ```bash
   # The service broadcasts: _miktos-camera._tcp.local.
   
   # Test discovery (macOS)
   dns-sd -B _miktos-camera._tcp.local.
   
   # Test discovery (Linux)
   avahi-browse -r _miktos-camera._tcp.local.
   ```

3. **Manual Registration**

   ```bash
   curl -X POST http://localhost:8000/api/cameras/register \
     -H "Content-Type: application/json" \
     -d '{
       "device_id": "camera-1",
       "name": "iPhone 13",
       "stream_url": "rtmp://192.168.1.100:1935/live"
     }'
   ```

4. **Check Firewall**

   ```bash
   # Allow mDNS (port 5353)
   sudo ufw allow 5353/udp
   ```

### Camera Connects Then Disconnects

**Symptoms:**

- Camera appears briefly
- Connection status changes to disconnected

**Solutions:**

- **Check WiFi signal strength**

- **Verify camera battery level**

- **Test stream URL manually**:

  ```bash
  ffplay rtmp://camera-ip:1935/live
  ```

- **Check camera app logs**

---

## Database Problems

### Database Locked

**Symptoms:**

- `database is locked` error
- Operations hang/timeout

**Solutions:**

```bash

# Find processes using database
fuser data/miktos_hub.db

# Kill process if stuck
fuser -k data/miktos_hub.db

# Restart server
python main.py

```

### Database Corruption

**Symptoms:**

- `malformed database` error
- Crashes on queries

**Solutions:**

```bash

# Backup current database
cp data/miktos_hub.db data/miktos_hub.db.backup

# Try to recover
sqlite3 data/miktos_hub.db ".dump" | sqlite3 data/miktos_hub_new.db
mv data/miktos_hub_new.db data/miktos_hub.db

# If recovery fails, start fresh
rm data/miktos_hub.db
python main.py

```

### Migration Errors

**Symptoms:**

- Schema mismatch errors
- Missing columns/tables

**Solutions:**

```bash

# Reset database (WARNING: loses data)
rm data/miktos_hub.db

# Or manually migrate (future feature)
# alembic upgrade head

```

---

## Performance Issues

### High CPU Usage

**Symptoms:**

- Server becomes slow
- CPU usage > 80%

**Solutions:**

1. **Check Active Sessions**

   ```bash
   curl http://localhost:8000/api/sessions/
   ```

2. **Stop Unused Sessions**

   ```bash
   curl -X DELETE http://localhost:8000/api/sessions/{session_id}
   ```

3. **Monitor Processes**

   ```bash
   htop
   # Look for miktos-hub processes
   ```

### High Memory Usage

**Symptoms:**

- Memory grows over time
- System becomes sluggish

**Solutions:**

```bash

# Check memory usage
ps aux | grep python

# Restart server periodically
systemctl restart miktos-hub

# Or configure memory limits in systemd
[Service]
MemoryLimit=512M

```

### Slow API Responses

**Symptoms:**

- API calls take > 1 second
- Timeouts

**Solutions:**

1. **Check Database Size**

   ```bash
   du -h data/miktos_hub.db
   # If > 100MB, consider cleanup
   ```

2. **Clear Old Sessions**

   ```bash
   # Delete sessions older than 30 days
   sqlite3 data/miktos_hub.db \
     "DELETE FROM sessions WHERE created_at < datetime('now', '-30 days');"
   ```

3. **Enable Caching** (future feature)

---

## API Errors

### 404 Not Found

**Symptom:**

```json
{"detail": "Not Found"}

```

**Solutions:**

- Verify endpoint exists: Check `/docs`
- Check URL spelling
- Ensure server is running on correct port

### 422 Unprocessable Entity

**Symptom:**

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

```

**Solutions:**

- Check required fields in request body
- Verify JSON structure matches schema
- See examples in `/docs`

### 500 Internal Server Error

**Symptom:**

```json
{"detail": "Internal Server Error"}

```

**Solutions:**

```bash

# Check server logs
tail -f /tmp/miktos.log

# Check systemd logs
journalctl -u miktos-hub -n 100

# Enable debug mode
export DEBUG=true
python main.py

```

### 503 Service Unavailable

**Symptom:**

```json
{"detail": "OBS Studio not connected"}

```

**Solutions:**

- See [OBS Connection](#obs-connection) section
- Verify OBS is running
- Check WebSocket configuration

---

## Logging & Debugging

### Enable Debug Logging

```python

# config/settings.py
logging:
    level: "DEBUG"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

```

### View Live Logs

```bash

# Development
tail -f /tmp/miktos.log

# Production (systemd)
journalctl -u miktos-hub -f

# Production (docker)
docker-compose logs -f miktos-hub

```

### Check Specific Module Logs

```bash

# Filter by module
journalctl -u miktos-hub | grep "obs_orchestrator"
journalctl -u miktos-hub | grep "session_manager"

```

---

## Getting Help

### Collect Diagnostic Information

```bash

#!/bin/bash
# diagnostic.sh - Collect system information

echo "=== Miktos Hub Diagnostics ==="
echo ""

echo "Python Version:"
python --version

echo ""
echo "Installed Packages:"
pip list | grep -E "fastapi|sqlalchemy|obs"

echo ""
echo "Server Status:"
curl -s http://localhost:8000/api/health | jq .

echo ""
echo "OBS Status:"
curl -s http://localhost:8000/api/obs/status | jq .

echo ""
echo "Recent Logs:"
tail -n 50 /tmp/miktos.log

echo ""
echo "System Resources:"
free -h
df -h

echo ""
echo "=== End Diagnostics ==="

```

### Report Issues

When reporting issues, include:

1. **Error message** (full stack trace)
2. **Steps to reproduce**

3. **System information** (OS, Python version)
4. **Diagnostic output** (run script above)
5. **Configuration** (sanitized settings)

**Submit to:** <https://github.com/LegnaPetiteTour/Miktos-Streamlab/issues>

---

## FAQ

**Q: Can I run multiple instances?**
A: Yes, use different ports and database files.

**Q: Does it work on Windows?**
A: Yes, but some paths need adjustment.

**Q: Can I use PostgreSQL instead of SQLite?**
A: Yes, update `DATABASE_URL` in config.

**Q: How do I upgrade?**
A: `git pull && pip install -r requirements.txt && systemctl restart miktos-hub`

**Q: Where are logs stored?**
A: `/tmp/miktos.log` (dev) or `/var/log/miktos-hub/` (production)
