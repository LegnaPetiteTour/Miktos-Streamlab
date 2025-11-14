# 🎯 Miktos Streamlab
**Professional Streaming Platform - Mobile + Desktop Unified Ecosystem**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Swift](https://img.shields.io/badge/Swift-5.8+-orange.svg)](https://swift.org)
[![Kotlin](https://img.shields.io/badge/Kotlin-1.9+-purple.svg)](https://kotlinlang.org)
[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)

> Transform any smartphone into a professional streaming camera with desktop-grade broadcasting infrastructure.

---

## 🌟 **What is Miktos Streamlab?**

Miktos Streamlab is a comprehensive streaming platform that bridges mobile convenience with professional broadcasting capabilities. It consists of native mobile apps (iOS & Android) that stream high-quality video to a powerful desktop platform for professional content creation and multi-destination broadcasting.

### **🎯 Key Value Proposition**
- **📱 Mobile Camera Apps** - Turn phones into professional streaming cameras
- **🖥️ Desktop Broadcasting Platform** - Enterprise-grade streaming infrastructure  
- **🔄 Seamless Integration** - Mobile streams directly integrate with desktop workflows
- **📺 Multi-Platform Output** - Simultaneous streaming to multiple destinations
- **⚡ Real-Time Processing** - Low-latency H.264/SRT streaming with quality monitoring

---

## ✨ **Features**

### � **Mobile Applications**
- **iOS Native App** (Swift/SwiftUI)
  - Hardware-accelerated H.264 encoding via VideoToolbox
  - SRT protocol for low-latency streaming
  - Real-time statistics and quality monitoring
  - Professional camera controls and settings

- **Android Native App** (Kotlin)
  - CameraX integration with MediaCodec encoding
  - TCP/UDP streaming protocols
  - Background service for reliable streaming
  - Adaptive bitrate and resolution controls

### 🖥️ **Desktop Platform** 
- **Python Backend** (25,881+ lines)
  - FastAPI web server with real-time APIs
  - OBS Studio WebSocket integration
  - Multi-destination streaming management
  - Quality analysis and performance monitoring
  - Failover systems and network resilience

- **Web Interface** (React/TypeScript)
  - Modern browser-based controls
  - Real-time stream monitoring dashboards
  - Multi-camera management interface
  - TailwindCSS responsive design

- **Infrastructure**
  - NGINX RTMP configuration
  - Automated deployment scripts
  - Docker containerization ready
  - Production monitoring and logging

---

## 🚀 **Quick Start**

### **Prerequisites**
- **iOS Development:** Xcode 14+, iOS 15+
- **Android Development:** Android Studio, API Level 24+
- **Desktop Platform:** Python 3.14+, Node.js 24+
- **Broadcasting:** OBS Studio 28+ (optional)

### **1. Mobile App Development**

#### iOS Setup
```bash
cd Mobile/iOS/Source/
# Open in Xcode and follow Documentation/Mobile/ guides
open StreamLabCamera.xcodeproj
```

#### Android Setup  
```bash
cd Mobile/Android/
# Open in Android Studio
./gradlew build
```

### **2. Desktop Platform Setup**

#### Backend
```bash
cd Desktop/Backend/
pip install -r requirements.txt
python3 main_hybrid.py  # Starts both desktop + web interfaces
```

#### Web Interface
```bash
cd Desktop/WebUI/
npm install
npm run dev  # Development server at http://localhost:5173
```

### **3. Start Streaming**
```bash
# Start desktop receiver
cd Mobile/Receivers/
python3 android_receiver.py

# Use mobile app to stream to receiver
# Configure OBS to receive from NGINX RTMP (optional)
```

---

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   📱 Mobile     │    │   🖥️ Desktop        │    │  📺 Broadcasting   │
│   Applications  │───▶│   Platform           │───▶│  Destinations       │
└─────────────────┘    └──────────────────────┘    └─────────────────────┘
│                      │                            │
├─ iOS Swift App       ├─ Python Backend           ├─ YouTube Live
├─ Android Kotlin      ├─ React Web UI             ├─ Twitch
└─ Desktop Receivers   ├─ OBS Integration          ├─ Facebook Live
                       └─ NGINX RTMP               └─ Custom RTMP
```

### **Data Flow**
1. **Mobile Capture** → Camera → H.264 Encoder → SRT/TCP Stream
2. **Desktop Reception** → Stream Decoder → Processing Pipeline → OBS
3. **Broadcasting** → OBS → NGINX RTMP → Multiple Destinations

---

## 📊 **Project Statistics**

| Component | Technology | Lines of Code | Status |
|-----------|------------|---------------|---------|
| iOS App | Swift/SwiftUI | 601 | ✅ Production Ready |
| Android App | Kotlin | 602 | ✅ Production Ready |
| Desktop Backend | Python | 25,881 | ✅ Production Ready |
| Web Interface | React/TypeScript | 254 | ✅ Production Ready |
| Scripts & Tools | Shell/Python | 1,280 | ✅ Production Ready |
| **Total** | **Mixed** | **28,618** | **✅ Production Ready** |

---

## 📂 **Project Structure**

```
Miktos-Streamlab/
├── 📱 Mobile/
│   ├── iOS/                    # Swift streaming application
│   │   ├── Source/            # Native Swift source code
│   │   ├── ProductionApp/     # Xcode project files
│   │   └── Archive/           # Legacy React Native archive
│   ├── Android/               # Kotlin streaming application
│   └── Receivers/             # Python desktop receivers
├── 🖥️ Desktop/
│   ├── Backend/               # Python streaming infrastructure
│   │   ├── core/             # Core streaming modules
│   │   ├── api/              # FastAPI web server
│   │   └── tests/            # Comprehensive test suite
│   ├── WebUI/                # React/TypeScript interface
│   ├── OBS-Integration/      # OBS Studio integration
│   └── Infrastructure/       # NGINX, deployment configs
├── 📚 Documentation/
│   ├── Mobile/               # iOS & Android setup guides
│   ├── Desktop/              # Backend & deployment guides
│   └── Brand/                # Architecture & roadmaps
└── 🛠️ Scripts/               # Build & utility scripts
```

---

## 🤝 **Contributing**

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### **Development Workflow**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 **Support**

- **Documentation:** [Documentation/](Documentation/)
- **Issues:** [GitHub Issues](https://github.com/LegnaPetiteTour/Miktos-Streamlab/issues)
- **Discussions:** [GitHub Discussions](https://github.com/LegnaPetiteTour/Miktos-Streamlab/discussions)

---

## 🎯 **Roadmap**

- [ ] **v2.0:** Multi-camera synchronization
- [ ] **v2.1:** Cloud-based processing pipeline  
- [ ] **v2.2:** AI-powered scene detection
- [ ] **v2.3:** WebRTC integration
- [ ] **v2.4:** Mobile app marketplace distribution

---

**Built with ❤️ for content creators and streaming professionals worldwide.**

---

[![GitHub stars](https://img.shields.io/github/stars/LegnaPetiteTour/Miktos-Streamlab?style=social)](https://github.com/LegnaPetiteTour/Miktos-Streamlab/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/LegnaPetiteTour/Miktos-Streamlab?style=social)](https://github.com/LegnaPetiteTour/Miktos-Streamlab/network/members)