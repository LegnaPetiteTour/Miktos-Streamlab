#!/bin/bash
# Simple E2E Test Runner

API="http://localhost:8000/api"

echo "=== Miktos Hub E2E Tests ==="
echo ""

# Test 1
echo "1. Server Health"
curl -s "$API/health" | jq -r '.overall_status'
echo ""

# Test 2
echo "2. Camera Count"
curl -s "$API/cameras/" | jq '. | length'
echo ""

# Test 3
echo "3. Create Session"
SESSION_DATA=$(curl -s -X POST "$API/sessions/" \
  -H "Content-Type: application/json" \
  -d '{"name":"E2E Test","description":"Automated test"}')
SESSION_ID=$(echo "$SESSION_DATA" | jq -r '.session_id')
echo "Session created: $SESSION_ID"
echo ""

# Test 4
echo "4. Get Session"
curl -s "$API/sessions/$SESSION_ID" | jq '{id, name, state}'
echo ""

# Test 5
echo "5. Start Session"
curl -s -X POST "$API/sessions/$SESSION_ID/start" \
  -H "Content-Type: application/json" \
  -d '{"start_streaming": false, "start_recording": false}' \
  | jq '{state, streaming_started, recording_started}'
echo ""

# Test 6
echo "6. Pause Session"
curl -s -X POST "$API/sessions/$SESSION_ID/pause" | jq '{state}'
echo ""

# Test 7
echo "7. Resume Session"
curl -s -X POST "$API/sessions/$SESSION_ID/resume" | jq '{state}'
echo ""

# Test 8
echo "8. End Session"
curl -s -X POST "$API/sessions/$SESSION_ID/end" | jq '{state}'
echo ""

# Test 9
echo "9. Database Check"
DB_PATH="$HOME/Desktop/Miktos Streamlab/data/miktos_hub.db"
if [ -f "$DB_PATH" ]; then
    COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions;" 2>/dev/null)
    echo "Sessions in DB: $COUNT"
else
    echo "DB not found"
fi
echo ""

# Test 10
echo "10. Delete Session"
curl -s -X DELETE "$API/sessions/$SESSION_ID" | jq '.'
echo ""

echo "=== Tests Complete ==="
