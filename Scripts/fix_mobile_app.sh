#!/bin/bash
# Fix Mobile App Build Issues - Miktos Streamlab
# This script fixes React Native/Expo Swift compatibility issues

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        Fixing Mobile App Build Issues                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")/StreamLabCamera"

echo "[1/5] Cleaning build artifacts..."
rm -rf ios/build
rm -rf ios/Pods
rm -rf node_modules/.cache
echo "✅ Build artifacts cleaned"
echo ""

echo "[2/5] Removing Podfile.lock..."
rm -f ios/Podfile.lock
echo "✅ Podfile.lock removed"
echo ""

echo "[3/5] Installing CocoaPods dependencies..."
cd ios
pod install --repo-update || pod install
cd ..
echo "✅ Pods installed"
echo ""

echo "[4/5] Cleaning Xcode derived data..."
rm -rf ~/Library/Developer/Xcode/DerivedData/StreamLabCamera-*
echo "✅ Derived data cleaned"
echo ""

echo "[5/5] Opening Xcode workspace..."
open ios/StreamLabCamera.xcworkspace
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  Build Fix Complete!                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📱 NEXT STEPS:"
echo "   1. Wait for Xcode to finish indexing (~2 minutes)"
echo "   2. Connect your physical iPhone"
echo "   3. Select your iPhone as the build target"
echo "   4. Click Product → Clean Build Folder (Cmd+Shift+K)"
echo "   5. Click Product → Build (Cmd+B)"
echo "   6. If successful, click Product → Run (Cmd+R)"
echo ""
echo "⚠️  IMPORTANT:"
echo "   • The app MUST run on a physical iPhone (not simulator)"
echo "   • Grant camera permissions when prompted"
echo "   • Make sure your iPhone and Mac are on the same WiFi"
echo ""
echo "🔧 TROUBLESHOOTING:"
echo "   • If build still fails, try: ./fix_mobile_app.sh"
echo "   • Check that Xcode Command Line Tools are installed:"
echo "     xcode-select --install"
echo ""
