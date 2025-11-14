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
