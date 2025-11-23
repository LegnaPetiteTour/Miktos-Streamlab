#!/bin/bash
# 🛠️ Fix Android Build Warnings - Miktos Streamlab
# This script fixes deprecated API usage and manifest warnings

set -e

ANDROID_PATH="/Users/atorrella/Desktop/Miktos/Mobile/Android"
MANIFEST_PATH="$ANDROID_PATH/app/src/main/AndroidManifest.xml"
CAMERA_STREAMER_PATH="$ANDROID_PATH/app/src/main/java/com/miktos/streamlabcamera/CameraStreamer.kt"

echo "🔧 Starting Android Build Warnings Fix..."

# Check if Android project exists
if [ ! -d "$ANDROID_PATH" ]; then
    echo "❌ Android project not found at: $ANDROID_PATH"
    exit 1
fi

# Fix 1: Remove deprecated package attribute from AndroidManifest.xml
echo "📝 Fix 1: Removing deprecated package attribute from AndroidManifest.xml"
if [ -f "$MANIFEST_PATH" ]; then
    # Create backup
    cp "$MANIFEST_PATH" "$MANIFEST_PATH.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Remove package attribute from manifest tag
    sed -i '' 's/package="[^"]*"//g' "$MANIFEST_PATH"
    echo "   ✅ AndroidManifest.xml package attribute removed"
else
    echo "   ❌ AndroidManifest.xml not found at: $MANIFEST_PATH"
fi

# Fix 2: Update deprecated createCaptureSession() API
echo "📝 Fix 2: Updating deprecated createCaptureSession() API"
if [ -f "$CAMERA_STREAMER_PATH" ]; then
    # Create backup
    cp "$CAMERA_STREAMER_PATH" "$CAMERA_STREAMER_PATH.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Check if file contains deprecated API
    if grep -q "createCaptureSession.*listOf.*StateCallback" "$CAMERA_STREAMER_PATH"; then
        echo "   ⚠️  Found deprecated createCaptureSession() usage"
        echo "   📋 Manual update required for CameraStreamer.kt:"
        echo "      - Add imports for OutputConfiguration, SessionConfiguration"
        echo "      - Replace deprecated createCaptureSession() with modern API"
        echo "      - See detailed instructions below"
    else
        echo "   ✅ No deprecated createCaptureSession() found"
    fi
else
    echo "   ❌ CameraStreamer.kt not found at: $CAMERA_STREAMER_PATH"
fi

echo ""
echo "🎯 MANUAL FIX REQUIRED for CameraStreamer.kt:"
echo "============================================="
echo ""
echo "ADD THESE IMPORTS (around line 10-15):"
echo "import android.hardware.camera2.params.OutputConfiguration"
echo "import android.hardware.camera2.params.SessionConfiguration"
echo "import java.util.concurrent.Executors"
echo ""
echo "REPLACE THIS (around line 157):"
echo "cameraDevice.createCaptureSession("
echo "    listOf(surface, encoderSurface),"
echo "    object : CameraCaptureSession.StateCallback() {"
echo "        // ... callbacks"
echo "    },"
echo "    null"
echo ")"
echo ""
echo "WITH THIS:"
echo "val outputConfigs = listOf("
echo "    OutputConfiguration(surface),"
echo "    OutputConfiguration(encoderSurface)"
echo ")"
echo ""
echo "val sessionConfig = SessionConfiguration("
echo "    SessionConfiguration.SESSION_REGULAR,"
echo "    outputConfigs,"
echo "    Executors.newSingleThreadExecutor(),"
echo "    object : CameraCaptureSession.StateCallback() {"
echo "        // ... same callbacks as before"
echo "    }"
echo ")"
echo ""
echo "cameraDevice.createCaptureSession(sessionConfig)"
echo ""
echo "🔄 After making manual changes, rebuild with:"
echo "cd $ANDROID_PATH"
echo "./gradlew clean assembleDebug installDebug"
echo ""
echo "✅ Build warnings should be resolved!"