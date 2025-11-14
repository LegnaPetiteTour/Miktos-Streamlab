#!/bin/bash
#
# Check SRT Failover Test Prerequisites
#

echo "============================================="
echo "SRT Failover Test - System Status Check"
echo "============================================="
echo ""

# Check SRT tools
echo "1. Checking SRT installation..."
if command -v srt-live-transmit &> /dev/null; then
    SRT_VERSION=$(srt-live-transmit -version 2>&1 | grep "SRT Library version" | head -1)
    echo "   ✅ SRT installed: $SRT_VERSION"
else
    echo "   ❌ SRT not found! Install with: brew install srt"
    exit 1
fi
echo ""

# Check NGINX
echo "2. Checking NGINX status..."
if pgrep nginx > /dev/null; then
    echo "   ✅ NGINX is running"
    
    # Check ports
    if sudo netstat -an | grep LISTEN | grep -q 1935; then
        echo "   ✅ RTMP port 1935 is listening"
    else
        echo "   ❌ RTMP port 1935 not listening!"
    fi
    
    if sudo netstat -an | grep LISTEN | grep -q 8080; then
        echo "   ✅ Stats port 8080 is listening"
    else
        echo "   ⚠️  Stats port 8080 not listening (optional)"
    fi
else
    echo "   ⚠️  NGINX is not running (will be used for testing)"
fi
echo ""

# Check .env configuration
echo "3. Checking .env configuration..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    
    if grep -q "SRT_BACKUP_URL=srt://" .env; then
        SRT_URL=$(grep "SRT_BACKUP_URL=" .env | cut -d'=' -f2)
        echo "   ✅ SRT_BACKUP_URL configured: $SRT_URL"
    else
        echo "   ❌ SRT_BACKUP_URL not configured in .env!"
        echo "      Add: SRT_BACKUP_URL=srt://localhost:9000?mode=caller"
        exit 1
    fi
    
    if grep -q "YOUTUBE_EN_STREAM_KEY=" .env && grep -q "YOUTUBE_FR_STREAM_KEY=" .env; then
        echo "   ✅ YouTube stream keys configured"
    else
        echo "   ⚠️  YouTube stream keys not fully configured"
    fi
else
    echo "   ❌ .env file not found!"
    exit 1
fi
echo ""

# Check test scripts
echo "4. Checking test scripts..."
if [ -x "./test_srt_receiver.sh" ]; then
    echo "   ✅ SRT receiver script ready"
else
    echo "   ❌ test_srt_receiver.sh not found or not executable"
fi

if [ -x "./run_failover_test.sh" ]; then
    echo "   ✅ Automated test script ready"
else
    echo "   ❌ run_failover_test.sh not found or not executable"
fi
echo ""

# Check Python environment
echo "5. Checking Python environment..."
if [ -f "./venv/bin/python" ]; then
    PYTHON_VERSION=$(./venv/bin/python --version)
    echo "   ✅ Virtual environment: $PYTHON_VERSION"
else
    echo "   ❌ Virtual environment not found at ./venv"
fi
echo ""

# Summary
echo "============================================="
echo "Prerequisites Summary"
echo "============================================="
echo ""
echo "Ready to test? Follow these steps:"
echo ""
echo "📌 Step 1: Start SRT receiver (Terminal 1)"
echo "   ./test_srt_receiver.sh 9000"
echo ""
echo "📌 Step 2: Start streaming application (Terminal 2)"
echo "   ./venv/bin/python src/main_hybrid.py --no-api | tee failover_test_log.txt"
echo ""
echo "📌 Step 3: Run automated failover test (Terminal 3)"
echo "   ./run_failover_test.sh"
echo ""
echo "Or see SRT_FAILOVER_TEST_GUIDE.md for manual testing steps"
echo ""
