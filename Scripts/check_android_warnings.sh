#!/bin/bash
# 🔍 Android Build Warnings Assessment - Miktos Streamlab
# This script checks for build warnings and provides exact fixes

set -e

ANDROID_PATH="/Users/atorrella/Desktop/Miktos/Mobile/Android"

echo "🔍 Analyzing Android Build Warnings..."
echo "======================================"

# Check project structure
if [ -d "$ANDROID_PATH" ]; then
    echo "✅ Android project found at: $ANDROID_PATH"
    
    # Check AndroidManifest.xml
    MANIFEST_PATH="$ANDROID_PATH/app/src/main/AndroidManifest.xml"
    if [ -f "$MANIFEST_PATH" ]; then
        echo "📋 Checking AndroidManifest.xml..."
        if grep -q 'package=' "$MANIFEST_PATH"; then
            echo "⚠️  FOUND: Deprecated package attribute in AndroidManifest.xml"
            echo "    Fix: Remove package=\"com.miktos.streamlabcamera\" from <manifest> tag"
        else
            echo "✅ AndroidManifest.xml looks clean (no deprecated package attribute)"
        fi
    else
        echo "❌ AndroidManifest.xml not found"
    fi
    
    # Check CameraStreamer.kt for deprecated API
    CAMERA_STREAMER_PATH="$ANDROID_PATH/app/src/main/java/com/miktos/streamlabcamera/CameraStreamer.kt"
    if [ -f "$CAMERA_STREAMER_PATH" ]; then
        echo "📋 Checking CameraStreamer.kt..."
        if grep -q "createCaptureSession.*listOf" "$CAMERA_STREAMER_PATH"; then
            echo "⚠️  FOUND: Deprecated createCaptureSession() API"
            echo "    Fix: Update to use SessionConfiguration instead of direct listOf()"
        else
            echo "✅ CameraStreamer.kt looks clean (modern API usage)"
        fi
    else
        echo "❌ CameraStreamer.kt not found"
    fi
    
    # Check build.gradle for namespace
    BUILD_GRADLE_PATH="$ANDROID_PATH/app/build.gradle.kts"
    if [ -f "$BUILD_GRADLE_PATH" ]; then
        echo "📋 Checking build.gradle.kts..."
        if grep -q "namespace.*com.miktos.streamlabcamera" "$BUILD_GRADLE_PATH"; then
            echo "✅ Namespace properly defined in build.gradle.kts"
        else
            echo "⚠️  Namespace might be missing from build.gradle.kts"
        fi
    fi
    
else
    echo "❌ Android project not found at: $ANDROID_PATH"
    echo "    Please verify the correct path to your Android project"
fi

echo ""
echo "🎯 QUICK FIXES:"
echo "==============="
echo ""
echo "1️⃣ ANDROIDMANIFEST.XML FIX:"
echo "   Edit: $ANDROID_PATH/app/src/main/AndroidManifest.xml"
echo "   Change: <manifest xmlns:android=\"...\" package=\"...\"> "
echo "   To:     <manifest xmlns:android=\"...\">"
echo "   (Just delete the package=\"...\" part)"
echo ""
echo "2️⃣ CAMERA API FIX:"
echo "   Edit: $ANDROID_PATH/app/src/main/java/com/miktos/streamlabcamera/CameraStreamer.kt"
echo "   Replace deprecated createCaptureSession() with SessionConfiguration"
echo "   (See detailed code in fix_android_warnings.sh)"
echo ""
echo "3️⃣ REBUILD:"
echo "   cd $ANDROID_PATH"
echo "   ./gradlew clean assembleDebug installDebug"
echo ""
echo "✅ These fixes should eliminate all build warnings!"