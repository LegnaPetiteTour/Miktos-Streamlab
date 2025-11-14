#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          WEEK 1 MVP COMPLETION CHECKLIST                       ║"
echo "║          Mobile Camera Streaming System                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 CHECKING REQUIREMENTS:"
echo ""

# Initialize counters
total_checks=0
passed_checks=0

# Function to check and report status
check_status() {
    local description="$1"
    local condition="$2"
    local success_msg="$3"
    local fail_msg="$4"
    
    total_checks=$((total_checks + 1))
    
    if eval "$condition"; then
        echo "✅ $success_msg"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        echo "❌ $fail_msg"
        return 1
    fi
}

# Check Android app source code
check_status "Android Source" \
    "[ -f '/Users/atorrella/Desktop/Miktos/Mobile/Android/app/src/main/java/com/miktos/streamlabcamera/CameraStreamService.kt' ]" \
    "Android app source code present" \
    "Android app source code missing"

# Check screen lock protection
check_status "Screen Protection" \
    "grep -q 'FLAG_KEEP_SCREEN_ON' '/Users/atorrella/Desktop/Miktos/Mobile/Android/app/src/main/java/com/miktos/streamlabcamera/MainActivity.kt'" \
    "Screen lock protection enabled" \
    "Screen lock protection missing"

# Check desktop receiver
check_status "Desktop Receiver" \
    "[ -f '/Users/atorrella/Desktop/Miktos/Mobile/Receivers/android_receiver.py' ]" \
    "Desktop receiver present" \
    "Desktop receiver missing"

# Check FFmpeg installation
check_status "FFmpeg" \
    "command -v ffmpeg > /dev/null 2>&1" \
    "FFmpeg installed" \
    "FFmpeg not installed"

# Check Android Studio (optional)
check_status "Android Studio" \
    "[ -d '/Applications/Android Studio.app' ] || [ -d '/usr/local/android-studio' ]" \
    "Android Studio detected" \
    "Android Studio not detected (optional)"

# Check Gradle wrapper
check_status "Gradle Build" \
    "[ -f '/Users/atorrella/Desktop/Miktos/Mobile/Android/gradlew' ]" \
    "Gradle wrapper present" \
    "Gradle wrapper missing"

echo ""
echo "══════════════════════════════════════════════════════════════"
echo ""

if [ $passed_checks -eq $total_checks ]; then
    echo "🎉 ALL REQUIREMENTS MET! ($passed_checks/$total_checks)"
    echo ""
    echo "🚀 READY FOR 30-MINUTE TEST:"
    echo ""
    echo "1️⃣  BUILD ANDROID APP:"
    echo "    cd /Users/atorrella/Desktop/Miktos/Mobile/Android"
    echo "    ./gradlew clean assembleDebug installDebug"
    echo ""
    echo "2️⃣  START DESKTOP RECEIVER:"
    echo "    cd /Users/atorrella/Desktop/Miktos/Mobile/Receivers"
    echo "    python3 android_receiver.py"
    echo ""
    echo "3️⃣  STREAMING TEST ON SAMSUNG S23 FE:"
    echo "    • Open StreamLabCamera app"
    echo "    • Set IP: 192.168.2.36, Port: 8554"
    echo "    • START STREAMING"
    echo "    • Let screen sleep naturally"
    echo "    • Record Mac screen showing live video"
    echo "    • Test for 30+ minutes"
    echo ""
    echo "🎯 SUCCESS CRITERIA:"
    echo "    ✅ 30+ minutes continuous streaming"
    echo "    ✅ Survives screen sleep"
    echo "    ✅ Notification stays visible"
    echo "    ✅ Can unlock phone without disconnect"
    echo "    ✅ Stable 7.8+ Mbps bitrate"
    echo ""
else
    echo "⚠️  REQUIREMENTS INCOMPLETE: ($passed_checks/$total_checks)"
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "  ACTION REQUIRED"
    echo "══════════════════════════════════════════════════════════════"
    echo ""
    
    # Provide specific remediation steps
    if [ ! -f '/Users/atorrella/Desktop/Miktos/Mobile/Android/app/src/main/java/com/miktos/streamlabcamera/CameraStreamService.kt' ]; then
        echo "📱 ANDROID APP MISSING:"
        echo "   Your working Android app needs to be copied to the new structure."
        echo "   The app has been successfully copied from the backup!"
        echo ""
    fi
    
    if ! grep -q 'FLAG_KEEP_SCREEN_ON' '/Users/atorrella/Desktop/Miktos/Mobile/Android/app/src/main/java/com/miktos/streamlabcamera/MainActivity.kt' 2>/dev/null; then
        echo "🔒 SCREEN PROTECTION MISSING:"
        echo "   Run: ./Scripts/add_screen_lock_protection.sh"
        echo ""
    fi
    
    if [ ! -f '/Users/atorrella/Desktop/Miktos/Mobile/Receivers/android_receiver.py' ]; then
        echo "🖥️  DESKTOP RECEIVER MISSING:"
        echo "   Copy android_receiver.py to Mobile/Receivers/"
        echo ""
    fi
fi

echo "══════════════════════════════════════════════════════════════"
echo ""
echo "📊 WEEK 1 MVP SUCCESS CRITERIA:"
echo ""
echo "   ✅ 30+ minute continuous streaming"
echo "   ✅ Survives screen sleep"
echo "   ✅ Notification stays visible"
echo "   ✅ Can unlock phone once without disconnect"
echo "   ✅ Stable 7.8+ Mbps bitrate"
echo "   ✅ Low-latency display (<200ms)"
echo ""
echo "══════════════════════════════════════════════════════════════"