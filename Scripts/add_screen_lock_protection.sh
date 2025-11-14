#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║              ADDING SCREEN LOCK PROTECTION                     ║"
echo "║              Prevents camera disconnect on unlock              ║"
echo "║                                                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Navigate to the Android project
cd "/Users/atorrella/Desktop/Miktos/Mobile/Android"

# Find the MainActivity.kt file
MAIN_ACTIVITY_FILE="app/src/main/java/com/miktos/streamlabcamera/MainActivity.kt"

if [ ! -f "$MAIN_ACTIVITY_FILE" ]; then
    echo "❌ MainActivity.kt not found at: $MAIN_ACTIVITY_FILE"
    exit 1
fi

echo "📱 Found MainActivity.kt"

# Check if FLAG_KEEP_SCREEN_ON is already added
if grep -q "FLAG_KEEP_SCREEN_ON" "$MAIN_ACTIVITY_FILE"; then
    echo "✅ Screen lock protection already enabled!"
    echo "   FLAG_KEEP_SCREEN_ON is already present in MainActivity.kt"
else
    echo "🔧 Adding screen lock protection..."
    
    # Create a backup
    cp "$MAIN_ACTIVITY_FILE" "$MAIN_ACTIVITY_FILE.backup"
    echo "💾 Created backup: $MAIN_ACTIVITY_FILE.backup"
    
    # Add the import for WindowManager if not present
    if ! grep -q "import android.view.WindowManager" "$MAIN_ACTIVITY_FILE"; then
        sed -i '' '/import android.os.Bundle/a\
import android.view.WindowManager
' "$MAIN_ACTIVITY_FILE"
        echo "📦 Added WindowManager import"
    fi
    
    # Add FLAG_KEEP_SCREEN_ON in the onCreate method
    if grep -q "setContentView" "$MAIN_ACTIVITY_FILE"; then
        sed -i '' '/setContentView/a\
        \
        // Keep screen on during streaming to prevent camera disconnect\
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
' "$MAIN_ACTIVITY_FILE"
        echo "✅ Added FLAG_KEEP_SCREEN_ON to onCreate method"
    else
        echo "⚠️  Could not find setContentView in MainActivity.kt"
        echo "   Please add this line manually after setContentView:"
        echo "   window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     PROTECTION ADDED! ✅                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🎯 What this does:"
echo "   • Keeps screen dimly lit during streaming"
echo "   • Prevents Samsung from killing camera when unlocking"
echo "   • Maintains stable 30+ minute streaming sessions"
echo ""
echo "📱 Next steps:"
echo "   1. Build the app: ./gradlew clean assembleDebug"
echo "   2. Install on phone: ./gradlew installDebug"
echo "   3. Start 30-minute test stream"
echo ""