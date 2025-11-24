#!/bin/bash
# Interactive E2E Testing Script
# Guides user through manual testing with real hardware

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_BASE="http://localhost:8000/api"

echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║     Miktos Hub Interactive E2E Testing                    ║
║     Real Camera + OBS + Streaming Platform                ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Helper function
prompt() {
    echo -e "${YELLOW}➜${NC} $1"
    read -p "Press Enter to continue..."
}

step() {
    echo ""
    echo -e "${GREEN}═══ $1 ═══${NC}"
    echo ""
}

# Step 1: Pre-flight checks
step "Step 1: Pre-flight Checks"
echo "Checking server health..."
HEALTH=$(curl -s "$API_BASE/health" | jq -r '.overall_status')
if [ "$HEALTH" == "healthy" ]; then
    echo "✓ Server is healthy"
else
    echo "✗ Server health issue: $HEALTH"
    exit 1
fi

OBS_STATUS=$(curl -s "$API_BASE/health" | jq -r '.components[] | select(.name == "OBS Engine") | .status')
if [ "$OBS_STATUS" == "healthy" ]; then
    echo "✓ OBS is connected"
else
    echo "✗ OBS not connected"
    echo "  Please ensure OBS is running with WebSocket enabled"
    exit 1
fi

prompt "Pre-flight checks complete"

# Step 2: Camera Discovery
step "Step 2: Camera Discovery"
echo "Checking for cameras..."
CAMERAS=$(curl -s "$API_BASE/cameras/")
CAMERA_COUNT=$(echo "$CAMERAS" | jq '. | length')

if [ "$CAMERA_COUNT" -eq 0 ]; then
    echo ""
    echo "No cameras discovered automatically."
    echo ""
    echo "Options:"
    echo "  1. Connect an iPhone with Miktos Camera app"
    echo "  2. Add an RTSP camera manually"
    echo "  3. Use a test stream URL"
    echo ""
    read -p "Which option? (1/2/3): " CAMERA_OPTION
    
    case $CAMERA_OPTION in
        1)
            echo ""
            echo "Please:"
            echo "  1. Open Miktos Camera app on iPhone"
            echo "  2. Ensure iPhone is on same WiFi network"
            echo "  3. Tap 'Start Broadcasting'"
            echo ""
            read -p "Press Enter when camera is broadcasting..."
            
            # Wait for discovery
            echo "Waiting for camera discovery (30 seconds)..."
            sleep 30
            
            CAMERAS=$(curl -s "$API_BASE/cameras/")
            CAMERA_COUNT=$(echo "$CAMERAS" | jq '. | length')
            ;;
        2)
            echo ""
            read -p "Enter RTSP URL (e.g., rtsp://192.168.1.100:8554/stream): " RTSP_URL
            read -p "Enter camera name: " CAMERA_NAME
            
            # Manual registration
            REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/cameras/register" \
                -H "Content-Type: application/json" \
                -d '{
                    "name": "'"$CAMERA_NAME"'",
                    "stream_url": "'"$RTSP_URL"'",
                    "type": "rtsp"
                }')
            
            CAMERA_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.id')
            echo "✓ Camera registered: $CAMERA_ID"
            ;;
        3)
            # Use test stream
            RTSP_URL="rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
            CAMERA_NAME="Test Stream (Big Buck Bunny)"
            
            REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/cameras/register" \
                -H "Content-Type: application/json" \
                -d '{
                    "name": "'"$CAMERA_NAME"'",
                    "stream_url": "'"$RTSP_URL"'",
                    "type": "rtsp"
                }')
            
            CAMERA_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.id')
            echo "✓ Test camera registered: $CAMERA_ID"
            ;;
    esac
    
    CAMERAS=$(curl -s "$API_BASE/cameras/")
    CAMERA_COUNT=$(echo "$CAMERAS" | jq '. | length')
fi

echo ""
echo "Available cameras:"
echo "$CAMERAS" | jq -r '.[] | "  - \(.name) (\(.id))"'
echo ""

CAMERA_ID=$(echo "$CAMERAS" | jq -r '.[0].id')
echo "Using camera: $CAMERA_ID"

prompt "Camera ready"

# Step 3: Create Session
step "Step 3: Create Production Session"
SESSION_NAME="E2E Test - $(date '+%Y-%m-%d %H:%M')"
echo "Creating session: $SESSION_NAME"

SESSION_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "'"$SESSION_NAME"'",
        "description": "Interactive E2E test session"
    }')

SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.session_id')
echo "✓ Session created: $SESSION_ID"

prompt "Session created"

# Step 4: Add Camera to Session
step "Step 4: Add Camera to Session"
echo "Adding camera $CAMERA_ID to session..."

ADD_CAMERA=$(curl -s -X POST "$API_BASE/sessions/$SESSION_ID/cameras" \
    -H "Content-Type: application/json" \
    -d '{
        "camera_id": "'"$CAMERA_ID"'",
        "position": 0
    }')

echo "✓ Camera added to session"
echo ""
echo "Session details:"
curl -s "$API_BASE/sessions/$SESSION_ID" | jq '.'

prompt "Camera added"

# Step 5: Configure OBS Scene
step "Step 5: Configure OBS Scene"
echo "Current OBS scenes:"
curl -s "$API_BASE/obs/scenes" | jq -r '.[] | "  - \(.name)"'
echo ""

echo "Now we'll add the camera as a source to OBS."
echo ""
read -p "Enter OBS scene name to use (or press Enter for current scene): " SCENE_NAME

if [ -z "$SCENE_NAME" ]; then
    SCENE_NAME=$(curl -s "$API_BASE/obs/scenes/current" | jq -r '.name')
    echo "Using current scene: $SCENE_NAME"
fi

echo ""
echo "📹 Manual step required:"
echo "  1. Open OBS Studio"
echo "  2. Go to scene: '$SCENE_NAME'"
echo "  3. Add source: 'Media Source' or 'VLC Video Source'"
echo "  4. Configure source with camera stream URL:"
echo ""
STREAM_URL=$(echo "$CAMERAS" | jq -r --arg id "$CAMERA_ID" '.[] | select(.id == $id) | .stream_url')
echo "     $STREAM_URL"
echo ""
echo "  5. Verify video is playing in OBS"
echo ""

prompt "OBS scene configured"

# Step 6: Configure Streaming Destination
step "Step 6: Configure Streaming Destination"
echo "Choose streaming platform:"
echo "  1. YouTube"
echo "  2. Twitch"
echo "  3. Custom RTMP"
echo "  4. Skip (test only)"
read -p "Choice (1-4): " PLATFORM_CHOICE

if [ "$PLATFORM_CHOICE" != "4" ]; then
    case $PLATFORM_CHOICE in
        1)
            PLATFORM="youtube"
            STREAM_URL_BASE="rtmp://a.rtmp.youtube.com/live2"
            echo ""
            echo "YouTube Streaming Setup:"
            echo "  1. Go to: https://studio.youtube.com/go/live"
            echo "  2. Copy your Stream Key"
            echo ""
            read -p "Paste YouTube Stream Key: " STREAM_KEY
            ;;
        2)
            PLATFORM="twitch"
            STREAM_URL_BASE="rtmp://live.twitch.tv/app"
            echo ""
            echo "Twitch Streaming Setup:"
            echo "  1. Go to: https://dashboard.twitch.tv/settings/stream"
            echo "  2. Copy your Stream Key"
            echo ""
            read -p "Paste Twitch Stream Key: " STREAM_KEY
            ;;
        3)
            PLATFORM="custom"
            read -p "Enter RTMP server URL: " STREAM_URL_BASE
            read -p "Enter stream key (if required): " STREAM_KEY
            ;;
    esac
    
    echo ""
    echo "Adding streaming destination..."
    curl -s -X POST "$API_BASE/sessions/$SESSION_ID/destinations" \
        -H "Content-Type: application/json" \
        -d '{
            "platform": "'"$PLATFORM"'",
            "stream_url": "'"$STREAM_URL_BASE"'",
            "stream_key": "'"$STREAM_KEY"'",
            "quality_preset": "1080p60"
        }' | jq '.'
    
    echo "✓ Streaming destination configured"
else
    echo "Skipping streaming configuration"
fi

prompt "Ready to start streaming"

# Step 7: Start Session
step "Step 7: Start Streaming"
echo "Starting session..."

START_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/$SESSION_ID/start")
echo "$START_RESPONSE" | jq '.'

echo ""
echo "✓ Session started!"
echo ""

if [ "$PLATFORM_CHOICE" != "4" ]; then
    echo "🎥 Your stream should now be live on $PLATFORM!"
    echo ""
    echo "Monitoring stream health for 60 seconds..."
    echo ""
    
    for i in {1..6}; do
        echo "Check $i/6..."
        HEALTH=$(curl -s "$API_BASE/sessions/$SESSION_ID/streaming/health")
        echo "$HEALTH" | jq '{status, bitrate, dropped_frames}'
        sleep 10
    done
fi

prompt "Stream is running"

# Step 8: Scene Switching (if multiple scenes)
step "Step 8: Scene Switching Test"
SCENE_COUNT=$(curl -s "$API_BASE/obs/scenes" | jq '. | length')

if [ "$SCENE_COUNT" -gt 1 ]; then
    echo "Testing scene switching..."
    echo ""
    curl -s "$API_BASE/obs/scenes" | jq -r '.[] | "  - \(.name)"'
    echo ""
    read -p "Enter scene name to switch to: " SWITCH_SCENE
    
    curl -s -X POST "$API_BASE/obs/scenes/current" \
        -H "Content-Type: application/json" \
        -d '{"scene_name": "'"$SWITCH_SCENE"'"}' | jq '.'
    
    echo "✓ Switched to scene: $SWITCH_SCENE"
else
    echo "Only one scene available, skipping scene switch test"
fi

prompt "Scene switching tested"

# Step 9: Test Session Pause/Resume
step "Step 9: Test Pause/Resume"
echo "Pausing session..."
curl -s -X POST "$API_BASE/sessions/$SESSION_ID/pause" | jq '.'
echo "✓ Session paused"
echo ""

sleep 3

echo "Resuming session..."
curl -s -X POST "$API_BASE/sessions/$SESSION_ID/resume" | jq '.'
echo "✓ Session resumed"

prompt "Pause/resume tested"

# Step 10: End Session
step "Step 10: End Session"
echo "Ending session..."
curl -s -X POST "$API_BASE/sessions/$SESSION_ID/end" | jq '.'
echo ""
echo "✓ Session ended"

prompt "Session ended"

# Step 11: Verify Persistence
step "Step 11: Verify Persistence"
echo "Checking database..."
DB_PATH="$HOME/Desktop/Miktos Streamlab/data/miktos_hub.db"

if [ -f "$DB_PATH" ]; then
    echo ""
    echo "Session in database:"
    sqlite3 "$DB_PATH" "SELECT id, name, state, created_at, ended_at FROM sessions WHERE id='$SESSION_ID';"
    echo ""
    echo "✓ Session persisted"
else
    echo "⚠ Database file not found"
fi

prompt "Testing complete"

# Summary
step "Test Summary"
echo ""
echo "✅ End-to-End Test Complete!"
echo ""
echo "Test Session ID: $SESSION_ID"
echo "Camera Used: $CAMERA_ID"
echo "Platform: ${PLATFORM:-none}"
echo ""
echo "Next steps:"
echo "  1. Review test results"
echo "  2. Check for any errors in server logs"
echo "  3. Verify stream recording/VOD on platform"
echo "  4. Test session recovery (restart server)"
echo ""
echo "Thank you for testing! 🎉"
