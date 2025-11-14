#!/bin/bash
# pivot_cleanup.sh - Remove municipal references and prepare for revolutionary platform

set -e

echo "🧹 MIKTOS STREAMLAB PIVOT CLEANUP"
echo "=================================="
echo ""
echo "This script will:"
echo "1. Remove all municipal/city/Ottawa references"
echo "2. Update project description to creator-focused"
echo "3. Clean up unnecessary files"
echo "4. Prepare for mobile camera development"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "📝 Step 1: Updating README.md..."
cat > README.md << 'EOF'
# Miktos StreamLab

> Revolutionary Live Streaming Platform with Mobile Camera Support

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Project Vision

Miktos StreamLab is the next-generation streaming platform that bridges the gap between hobbyist tools and broadcast systems. Use your phones as professional wireless cameras, stream to multiple platforms simultaneously with automatic vertical output, and edit your content with AI-powered tools—all in one application.

### Revolutionary Features

#### 🎥 Mobile Camera System (In Development - Week 1)
- **Phone-as-Camera**: Use your smartphones as wireless professional cameras
- **Multi-Angle Support**: Connect 2-3+ phones simultaneously
- **Low Latency**: <150ms from phone to OBS (<200ms end-to-end)
- **QR Code Pairing**: Instant phone-to-desktop connection
- **Studio Mode**: Do Not Disturb, power management, thermal control

#### 📱 Vertical Simulcast (Coming - Week 5-8)
- **Automatic 9:16 Output**: Stream horizontal AND vertical simultaneously
- **AI Face Tracking**: Auto-crop with intelligent framing
- **Multi-Platform**: YouTube 16:9 + TikTok/Instagram 9:16 from one source
- **Zero Manual Work**: No separate vertical scenes needed

#### ✂️ Post-Production Suite (Coming - Week 9-14)
- **Integrated Editor**: Timeline editing with FFmpeg backend
- **AI Highlights**: Automatically detect best moments
- **Auto-Reel Generator**: Create 30s/60s clips for social media
- **Transcript Integration**: Click-to-seek from AI transcription
- **One-Click Publish**: Export directly to YouTube, TikTok, Instagram

#### 🎛️ Production Intelligence
- **Confidence Monitor**: Preview your stream without opening a browser
- **AI Operator Hints**: Real-time suggestions for audio/video quality
- **Bitrate Governor**: Automatic quality adaptation for network changes
- **Safe Slate Automation**: Professional failover handling
- **Pre-Flight Checks**: Comprehensive validation before going live

### Core Features (Already Built)

- 🎬 **OBS Integration** - Professional WebSocket 5.x control
- 🌐 **Network Monitoring** - Real-time connection quality analysis  
- 📊 **Stream Health Dashboard** - Live metrics and alerts
- 🎯 **Multi-Platform Streaming** - YouTube, Facebook, Twitter support
- 🎨 **Professional Transitions** - Automated intro/outro sequences
- 📝 **AI Transcription** - Real-time speech-to-text

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OBS Studio 28.0+
- OBS WebSocket Plugin 5.0+
- FFmpeg (with SRT support)
- For mobile cameras: Physical iOS or Android device

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/miktos-streamlab.git
cd miktos-streamlab

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run hybrid UI
python src/main_hybrid.py
```

## 📖 Documentation

- [Quick Start Guide](docs/user/QUICK_START.md)
- [Week 1 Action Plan](WEEK_1_ACTION_PLAN.md) - Mobile Camera MVP
- [Full Roadmap](PIVOT_ROADMAP.md) - 20-week plan
- [Architecture](docs/development/ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)

## 🎯 Current Status

**Phase**: Pivot to Revolutionary Platform  
**Week**: 1 (Mobile Camera MVP)  
**Focus**: Phone-to-desktop wireless camera system

See [PIVOT_ROADMAP.md](PIVOT_ROADMAP.md) for detailed 20-week plan.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👥 Creator

**Lead Developer**: Alex Torrella  
**Vision**: Bridge the gap between OBS and professional broadcast systems

---

Built for creators who demand more than basic streaming tools 🚀
EOF

echo "✅ README.md updated"

echo ""
echo "📝 Step 2: Cleaning up doc references..."

# Update or remove municipal-specific docs
if [ -d "docs" ]; then
    find docs -type f -name "*.md" -exec sed -i '' 's/municipal/creator/gi' {} \;
    find docs -type f -name "*.md" -exec sed -i '' 's/City of Ottawa/Miktos StreamLab/g' {} \;
    find docs -type f -name "*.md" -exec sed -i '' 's/Ottawa/streaming platform/g' {} \;
    echo "✅ Documentation cleaned"
fi

echo ""
echo "📝 Step 3: Updating source code comments..."

# Remove municipal references from Python files
find src -type f -name "*.py" -exec sed -i '' 's/municipal/streaming/gi' {} \;
find src -type f -name "*.py" -exec sed -i '' 's/City of Ottawa/Miktos StreamLab/g' {} \;

echo "✅ Source code updated"

echo ""
echo "📝 Step 4: Creating mobile app directory structure..."

mkdir -p mobile-app/ios
mkdir -p mobile-app/android
mkdir -p mobile-app/src/components
mkdir -p mobile-app/src/services
mkdir -p mobile-app/src/utils

echo "✅ Mobile app structure created"

echo ""
echo "📝 Step 5: Creating placeholder files..."

cat > mobile-app/README.md << 'EOF'
# Miktos StreamLab - Mobile Camera App

React Native application that turns your phone into a professional wireless camera.

## Features
- H.264 hardware encoding
- SRT streaming
- QR code pairing
- Studio mode (DND, power management)

## Setup
```bash
cd mobile-app
npm install
npx react-native run-ios     # iOS
npx react-native run-android # Android
```

See [Week 1 Action Plan](../WEEK_1_ACTION_PLAN.md) for development roadmap.
EOF

cat > src/mobile/__init__.py << 'EOF'
"""
Mobile camera integration module.

Handles SRT streams from mobile phones acting as wireless cameras.
"""
EOF

cat > src/mobile/srt_receiver.py << 'EOF'
"""
SRT receiver for mobile camera streams.

Accepts SRT connections from mobile phones and exposes them as
virtual cameras to OBS via NDI or v4l2loopback.
"""
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class CameraStream:
    """Represents a mobile camera stream"""
    phone_id: str
    resolution: str
    fps: int
    bitrate: int
    latency_ms: float
    connected: bool


class MobileCameraReceiver:
    """
    Receives SRT streams from mobile phones.
    
    Usage:
        receiver = MobileCameraReceiver(port=9001)
        await receiver.start_listening()
    """
    
    def __init__(self, port: int = 9001):
        self.port = port
        self.cameras: Dict[str, CameraStream] = {}
    
    async def start_listening(self):
        """Start accepting SRT connections"""
        # TODO: Implement SRT server
        # TODO: Decode H.264 streams
        # TODO: Expose as NDI or virtual camera
        pass
    
    def get_active_cameras(self) -> list[CameraStream]:
        """Return list of currently connected cameras"""
        return [cam for cam in self.cameras.values() if cam.connected]
EOF

echo "✅ Placeholder files created"

echo ""
echo "📝 Step 6: Updating .gitignore..."

cat >> .gitignore << 'EOF'

# Mobile app
mobile-app/node_modules/
mobile-app/ios/Pods/
mobile-app/.expo/
mobile-app/android/.gradle/
mobile-app/android/app/build/

# React Native
*.jsbundle
*.bundle
.expo-shared/
EOF

echo "✅ .gitignore updated"

echo ""
echo "🎉 CLEANUP COMPLETE!"
echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Read PIVOT_ROADMAP.md for full 20-week plan"
echo "3. Start Week 1: Follow WEEK_1_ACTION_PLAN.md"
echo "4. Focus: Build mobile camera MVP (phone → desktop → OBS)"
echo ""
echo "🚀 Your revolutionary platform starts now!"
