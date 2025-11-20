#!/bin/bash
# Quick Reference: Desktop Control Panel

cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          📹 Miktos StreamLab - Control Panel                   ║
║                   Quick Reference Card                         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

🚀 START THE CONTROL PANEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  cd Desktop/Backend/remote_control
  ./start_control_panel.sh

  Then open: http://localhost:5000


📱 CONNECT ANDROID PHONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Open app → Settings
  2. Remote Control → Enable
  3. Server IP: 192.168.2.36
  4. Port: 9000
  5. Tap "Connect"


🎮 CONTROL BUTTONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ▶️  START       - Begin streaming
  ⏹️  STOP        - Stop streaming
  ⏸️  PAUSE       - Freeze frame (connection alive)
  ▶️  RESUME      - Resume from pause
  🌙 Studio Mode - Black screen with red dot
  🔄 Refresh     - Update status


📊 STATUS INDICATORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  State Colors:
    🟢 Green pulse  = STREAMING
    🟠 Orange       = PAUSED
    🔴 Red          = OFFLINE
    ⚪ Gray         = IDLE

  Icons:
    🔋 Battery      📶 WiFi         📱 LTE
    ⚡ Charging     ✅ Thermal OK   🌡️ Warm
    🔥 Hot          ☠️  Critical


🔧 TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Camera not appearing?
    → Check phone shows "connected"
    → Verify IP address (use Mac local IP, not 127.0.0.1)
    → Check firewall settings

  Commands not working?
    → Verify camera shows "online" in web UI
    → Check browser console (F12)
    → Restart servers: ./start_control_panel.sh

  Status not updating?
    → Click "Refresh" button
    → Check Android app logs
    → Verify WebSocket connection


📁 IMPORTANT FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Desktop/Backend/remote_control/
    ├── start_control_panel.sh    (Start script)
    ├── control_panel.py          (Flask server)
    ├── websocket_server.py       (WebSocket server)
    └── templates/
        └── control_panel.html    (Web UI)

  Documentation/Desktop/
    └── CONTROL_PANEL_GUIDE.md    (Full guide)


🌐 NETWORK CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Required Ports:
    9000  - Camera WebSocket connections
    9001  - Controller WebSocket connections
    5000  - Web UI (HTTP)

  Find your Mac IP:
    ifconfig | grep "inet "
    → Look for 192.168.x.x


✅ TESTING CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [ ] Control panel starts successfully
  [ ] Web UI loads at http://localhost:5000
  [ ] Android phone connects (camera card appears)
  [ ] START command works (streaming begins)
  [ ] STOP command works (streaming ends)
  [ ] PAUSE command works (freeze frame)
  [ ] RESUME command works (instant recovery)
  [ ] Studio Mode works (black screen + red dot)
  [ ] Status updates appear (battery, network, thermal)
  [ ] Multiple cameras work independently


📞 HELP & DOCS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Full Guide:
    Documentation/Desktop/CONTROL_PANEL_GUIDE.md

  Implementation Status:
    CONTROL_PANEL_COMPLETE.md

  Test System:
    python3 test_control_panel.py


═══════════════════════════════════════════════════════════════════

         Status: ✅ READY FOR TESTING
         Version: 1.0.0 (November 18, 2025)

═══════════════════════════════════════════════════════════════════

EOF
