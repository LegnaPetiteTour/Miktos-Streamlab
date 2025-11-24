#!/bin/bash
# End-to-End Testing Script for Miktos Hub
# Tests complete workflow with real cameras and streaming

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000/api"
TEST_LOG="/tmp/miktos_e2e_test.log"
RESULTS_FILE="/tmp/miktos_e2e_results.txt"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$TEST_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$TEST_LOG"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$TEST_LOG"
    ((TESTS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1" | tee -a "$TEST_LOG"
}

test_start() {
    ((TESTS_TOTAL++))
    log_info "Test $TESTS_TOTAL: $1"
}

# Clear previous test logs
> "$TEST_LOG"
> "$RESULTS_FILE"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Miktos Hub End-to-End Testing Suite                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Server Health Check
test_start "Server health check"
HEALTH_RESPONSE=$(curl -s "$API_BASE/health" || echo "FAILED")
if echo "$HEALTH_RESPONSE" | jq -e '.overall_status == "healthy"' > /dev/null 2>&1; then
    log_success "Server is healthy"
else
    log_error "Server health check failed"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

# Test 2: Camera Discovery
test_start "Camera discovery status"
CAMERA_COUNT=$(curl -s "$API_BASE/cameras/" | jq '. | length' || echo 0)
log_info "Discovered $CAMERA_COUNT camera(s)"
if [ "$CAMERA_COUNT" -gt 0 ]; then
    log_success "Camera discovery working"
    FIRST_CAMERA_ID=$(curl -s "$API_BASE/cameras/" | jq -r '.[0].id')
    log_info "First camera ID: $FIRST_CAMERA_ID"
else
    log_warning "No cameras discovered - will test with mock camera"
    FIRST_CAMERA_ID="mock-camera-1"
fi

# Test 3: Create Session
test_start "Create production session"
SESSION_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "E2E Test Session - '"$(date +%Y%m%d_%H%M%S)"'",
        "description": "Automated end-to-end test session"
    }')

SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.session_id')
if [ "$SESSION_ID" != "null" ] && [ -n "$SESSION_ID" ]; then
    log_success "Session created: $SESSION_ID"
    echo "$SESSION_ID" > /tmp/e2e_session_id.txt
else
    log_error "Failed to create session"
    echo "Response: $SESSION_RESPONSE"
    exit 1
fi

# Test 4: Verify Session Persistence
test_start "Verify session persisted to database"
DB_PATH="$HOME/Desktop/Miktos Streamlab/data/miktos_hub.db"
if [ -f "$DB_PATH" ]; then
    DB_SESSION=$(sqlite3 "$DB_PATH" "SELECT id FROM sessions WHERE id='$SESSION_ID';" 2>/dev/null || echo "")
    if [ "$DB_SESSION" == "$SESSION_ID" ]; then
        log_success "Session found in database"
    else
        log_error "Session NOT found in database"
    fi
else
    log_warning "Database file not found at $DB_PATH"
fi

# Test 5: Add Camera to Session
if [ "$CAMERA_COUNT" -gt 0 ]; then
    test_start "Add camera to session"
    ADD_CAMERA_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/$SESSION_ID/cameras" \
        -H "Content-Type: application/json" \
        -d '{
            "camera_id": "'"$FIRST_CAMERA_ID"'",
            "position": 0
        }' || echo "FAILED")
    
    if echo "$ADD_CAMERA_RESPONSE" | jq -e '.camera_id' > /dev/null 2>&1; then
        log_success "Camera added to session"
    else
        log_error "Failed to add camera to session"
        echo "Response: $ADD_CAMERA_RESPONSE"
    fi
else
    log_warning "Skipping camera add test - no cameras available"
fi

# Test 6: Get Session Details
test_start "Retrieve session details"
SESSION_DETAILS=$(curl -s "$API_BASE/sessions/$SESSION_ID")
SESSION_NAME=$(echo "$SESSION_DETAILS" | jq -r '.name')
SESSION_STATE=$(echo "$SESSION_DETAILS" | jq -r '.state')
if [ "$SESSION_STATE" != "null" ]; then
    log_success "Session details retrieved (State: $SESSION_STATE)"
else
    log_error "Failed to retrieve session details"
fi

# Test 7: OBS Connection
test_start "OBS connection status"
OBS_STATUS=$(curl -s "$API_BASE/health" | jq -r '.components[] | select(.name == "OBS Engine") | .status')
if [ "$OBS_STATUS" == "healthy" ]; then
    log_success "OBS is connected"
else
    log_warning "OBS connection issue (Status: $OBS_STATUS)"
fi

# Test 8: List OBS Scenes
test_start "List OBS scenes"
OBS_SCENES=$(curl -s "$API_BASE/obs/scenes" || echo "[]")
SCENE_COUNT=$(echo "$OBS_SCENES" | jq '. | length' || echo 0)
if [ "$SCENE_COUNT" -gt 0 ]; then
    log_success "OBS has $SCENE_COUNT scene(s)"
    FIRST_SCENE=$(echo "$OBS_SCENES" | jq -r '.[0].name')
    log_info "First scene: $FIRST_SCENE"
else
    log_warning "No OBS scenes found"
fi

# Test 9: Get Current Scene
test_start "Get current OBS scene"
CURRENT_SCENE=$(curl -s "$API_BASE/obs/scenes/current" | jq -r '.name' || echo "unknown")
if [ "$CURRENT_SCENE" != "null" ] && [ -n "$CURRENT_SCENE" ]; then
    log_success "Current scene: $CURRENT_SCENE"
else
    log_warning "Could not get current scene"
fi

# Test 10: Session State Transition
test_start "Test session state transition (start)"
START_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/$SESSION_ID/start" || echo "FAILED")
if echo "$START_RESPONSE" | jq -e '.state' > /dev/null 2>&1; then
    NEW_STATE=$(echo "$START_RESPONSE" | jq -r '.state')
    log_success "Session started (New state: $NEW_STATE)"
    
    # Verify state persisted
    sleep 2
    if [ -f "$DB_PATH" ]; then
        DB_STATE=$(sqlite3 "$DB_PATH" "SELECT state FROM sessions WHERE id='$SESSION_ID';" 2>/dev/null || echo "")
        if [ "$DB_STATE" == "$NEW_STATE" ]; then
            log_success "State change persisted to database"
        else
            log_error "State NOT persisted (DB: $DB_STATE, Expected: $NEW_STATE)"
        fi
    fi
else
    log_error "Failed to start session"
    echo "Response: $START_RESPONSE"
fi

# Test 11: List All Sessions
test_start "List all sessions"
ALL_SESSIONS=$(curl -s "$API_BASE/sessions/" || echo "[]")
SESSION_COUNT=$(echo "$ALL_SESSIONS" | jq '. | length' || echo 0)
if [ "$SESSION_COUNT" -gt 0 ]; then
    log_success "Found $SESSION_COUNT session(s)"
else
    log_error "No sessions found"
fi

# Test 12: Pause Session
test_start "Pause session"
PAUSE_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/$SESSION_ID/pause" || echo "FAILED")
if echo "$PAUSE_RESPONSE" | jq -e '.state == "paused"' > /dev/null 2>&1; then
    log_success "Session paused"
else
    log_warning "Session pause may have failed"
fi

# Test 13: Resume Session
test_start "Resume session"
RESUME_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/$SESSION_ID/resume" || echo "FAILED")
if echo "$RESUME_RESPONSE" | jq -e '.state' > /dev/null 2>&1; then
    log_success "Session resumed"
else
    log_warning "Session resume may have failed"
fi

# Test 14: End Session
test_start "End session"
END_RESPONSE=$(curl -s -X POST "$API_BASE/sessions/$SESSION_ID/end" || echo "FAILED")
if echo "$END_RESPONSE" | jq -e '.state' > /dev/null 2>&1; then
    END_STATE=$(echo "$END_RESPONSE" | jq -r '.state')
    log_success "Session ended (Final state: $END_STATE)"
else
    log_error "Failed to end session"
fi

# Test 15: Delete Session
test_start "Delete session"
DELETE_RESPONSE=$(curl -s -X DELETE "$API_BASE/sessions/$SESSION_ID" || echo "FAILED")
if echo "$DELETE_RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
    log_success "Session deleted"
    
    # Verify deleted from database
    if [ -f "$DB_PATH" ]; then
        DB_CHECK=$(sqlite3 "$DB_PATH" "SELECT id FROM sessions WHERE id='$SESSION_ID';" 2>/dev/null || echo "")
        if [ -z "$DB_CHECK" ]; then
            log_success "Session removed from database"
        else
            log_error "Session still exists in database"
        fi
    fi
else
    log_error "Failed to delete session"
fi

# Test Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Test Summary                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Total Tests: $TESTS_TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

# Calculate success rate
SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED/$TESTS_TOTAL)*100}")
echo "Success Rate: $SUCCESS_RATE%"
echo ""

# Save results
cat > "$RESULTS_FILE" << EOF
Miktos Hub E2E Test Results
===========================
Date: $(date)
Total Tests: $TESTS_TOTAL
Passed: $TESTS_PASSED
Failed: $TESTS_FAILED
Success Rate: $SUCCESS_RATE%

Full log: $TEST_LOG
EOF

echo "Results saved to: $RESULTS_FILE"
echo "Full log: $TEST_LOG"
echo ""

# Exit with appropriate code
if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
fi
