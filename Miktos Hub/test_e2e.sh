#!/bin/bash

# E2E Test Script for Miktos Hub
# This script helps validate the critical E2E workflow

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Miktos Hub E2E Validation Test"
echo "=========================================="
echo ""

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

# Function to print info
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

echo "Test 1: Server Health Check"
echo "----------------------------"
HEALTH=$(curl -s $BASE_URL/api/health/ping)
if echo "$HEALTH" | grep -q "pong"; then
    print_result 0 "Server is running and responding"
else
    print_result 1 "Server is not responding"
    exit 1
fi
echo ""

echo "Test 2: OBS Connection Status"
echo "------------------------------"
OBS_STATUS=$(curl -s $BASE_URL/api/obs/status)

OBS_CONNECTED=$(echo "$OBS_STATUS" | python3 -c "import sys, json; print(str(json.load(sys.stdin).get('connected', False)).lower())")

if [ "$OBS_CONNECTED" = "true" ]; then
    print_result 0 "OBS is connected"
    OBS_VERSION=$(echo "$OBS_STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))")
    print_info "OBS Version: $OBS_VERSION"
    echo "$OBS_STATUS" | python3 -m json.tool
else
    print_result 1 "OBS is not connected"
    print_info "Please ensure OBS Studio is running with obs-websocket enabled"
    echo ""
    print_info "To enable obs-websocket:"
    echo "  1. Open OBS Studio"
    echo "  2. Go to Tools → obs-websocket Settings"
    echo "  3. Check 'Enable WebSocket server'"
    echo "  4. Use default port 4455"
    exit 1
fi
echo ""

echo "Test 3: OBS Scenes"
echo "------------------"
SCENES=$(curl -s $BASE_URL/api/obs/scenes)
SCENE_COUNT=$(echo "$SCENES" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))")

if [ "$SCENE_COUNT" -gt 0 ]; then
    print_result 0 "Found $SCENE_COUNT scene(s)"
    echo "$SCENES" | python3 -m json.tool
else
    print_result 1 "No scenes found in OBS"
    print_info "Please create test scenes in OBS Studio:"
    echo ""
    echo "  Scene 1: 'Main Camera'"
    echo "    - Add a Video Capture Device source"
    echo ""
    echo "  Scene 2: 'Picture-in-Picture'"
    echo "    - Add two Video Capture Device sources"
    echo ""
    echo "  Scene 3: 'Screen Share'"
    echo "    - Add a Display Capture source"
    echo ""
    print_info "After creating scenes, run this script again"
    exit 0
fi
echo ""

echo "Test 4: Scene Switching"
echo "-----------------------"
if [ "$SCENE_COUNT" -gt 1 ]; then
    # Get first scene name
    FIRST_SCENE=$(echo "$SCENES" | python3 -c "import sys, json; scenes = json.load(sys.stdin)['scenes']; print(scenes[0]['name'] if scenes else '')")
    
    if [ -n "$FIRST_SCENE" ]; then
        print_info "Attempting to switch to scene: $FIRST_SCENE"
        
        # URL encode the scene name
        ENCODED_SCENE=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$FIRST_SCENE'))")
        
        SWITCH_RESULT=$(curl -s -X POST "$BASE_URL/api/obs/scenes/$ENCODED_SCENE/activate")
        
        if echo "$SWITCH_RESULT" | grep -q "success\|Success"; then
            print_result 0 "Scene switched successfully"
        else
            print_result 1 "Scene switch failed"
            echo "Response: $SWITCH_RESULT"
        fi
    fi
else
    print_info "Need at least 2 scenes to test switching"
fi
echo ""

echo "Test 5: Camera Discovery"
echo "------------------------"
CAMERAS=$(curl -s $BASE_URL/api/cameras/)
CAMERA_COUNT=$(echo "$CAMERAS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))")

if [ "$CAMERA_COUNT" -gt 0 ]; then
    print_result 0 "Found $CAMERA_COUNT camera(s)"
    echo "$CAMERAS" | python3 -m json.tool
else
    print_info "No cameras discovered yet"
    print_info "You can start discovery with:"
    echo "  curl -X POST $BASE_URL/api/cameras/discovery/start -H 'Content-Type: application/json' -d '{\"timeout_seconds\": 30}'"
fi
echo ""

echo "Test 6: Session Management"
echo "--------------------------"
SESSIONS=$(curl -s $BASE_URL/api/sessions/)
SESSION_COUNT=$(echo "$SESSIONS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))")

if [ "$SESSION_COUNT" -gt 0 ]; then
    print_result 0 "Found $SESSION_COUNT session(s)"
    echo "$SESSIONS" | python3 -m json.tool
else
    print_info "No sessions created yet"
    print_info "Create a test session with:"
    echo "  curl -X POST $BASE_URL/api/sessions/ -H 'Content-Type: application/json' -d '{\"name\": \"Test Session\", \"description\": \"E2E validation test\"}'"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

if [ "$SCENE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Ready to proceed with E2E testing${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure streaming destination (YouTube/Twitch/Local RTMP)"
    echo "  2. Run full production workflow test"
    echo "  3. See docs/E2E_CRITICAL_VALIDATION.md for detailed steps"
else
    echo -e "${YELLOW}⚠ Setup incomplete${NC}"
    echo ""
    echo "Required actions:"
    echo "  1. Create test scenes in OBS Studio"
    echo "  2. Run this script again to verify"
fi

echo ""
