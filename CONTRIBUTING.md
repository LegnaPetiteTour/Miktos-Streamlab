# Contributing to Miktos Streamlab

Thank you for your interest in contributing to Miktos Streamlab! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use GitHub Issues to report bugs or request features
- Search existing issues before creating new ones
- Provide detailed information including:
  - Operating system and version
  - Device information (for mobile issues)
  - Steps to reproduce
  - Expected vs actual behavior
  - Screenshots or logs when applicable

### Pull Requests
1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Test thoroughly
5. Update documentation if needed
6. Submit a pull request with a clear description

## 🏗️ Development Setup

### Prerequisites
- **iOS:** Xcode 14+, iOS 15+
- **Android:** Android Studio, API Level 24+
- **Backend:** Python 3.14+, pip
- **Frontend:** Node.js 24+, npm
- **Broadcasting:** OBS Studio 28+ (optional)

### Local Development
```bash
# Clone repository
git clone https://github.com/LegnaPetiteTour/Miktos-Streamlab.git
cd Miktos-Streamlab

# Backend setup
cd Desktop/Backend
pip install -r requirements.txt
python3 main.py

# Frontend setup
cd ../WebUI
npm install
npm run dev

# Mobile development
# iOS: Open Mobile/iOS/Source in Xcode
# Android: Open Mobile/Android in Android Studio
```

## 📝 Code Standards

### General
- Write clear, self-documenting code
- Add comments for complex logic
- Follow existing code style in each language
- Include unit tests for new features

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints
- Maximum line length: 88 characters (Black formatter)
- Use docstrings for functions and classes
- Run tests with `pytest`

### Swift (iOS)
- Follow Swift API Design Guidelines
- Use SwiftUI for UI components
- Document public APIs
- Use meaningful variable and function names

### Kotlin (Android)
- Follow Kotlin coding conventions
- Use Jetpack Compose for UI (when applicable)
- Follow Material Design principles
- Use dependency injection where appropriate

### TypeScript/React (Web)
- Follow TypeScript strict mode
- Use functional components with hooks
- Follow ESLint configuration
- Use Prettier for formatting

## 🧪 Testing

### Running Tests
```bash
# Python backend tests
cd Desktop/Backend
pytest

# Web interface tests
cd Desktop/WebUI
npm test

# Mobile app tests
# iOS: Run tests in Xcode (Cmd+U)
# Android: ./gradlew test
```

### Test Guidelines
- Write tests for all new features
- Maintain minimum 80% code coverage
- Include integration tests for API endpoints
- Test mobile apps on multiple devices/simulators

## 📱 Mobile Development

### iOS Guidelines
- Support iOS 15+
- Use AVFoundation for camera access
- Implement proper error handling
- Test on physical devices when possible
- Follow Apple's Human Interface Guidelines

### Android Guidelines
- Support API Level 24+
- Use CameraX for camera functionality
- Follow Material Design principles
- Test on various screen sizes
- Handle different Android versions gracefully

## 🖥️ Desktop Development

### Backend Guidelines
- Use FastAPI for web APIs
- Implement proper error handling and logging
- Use async/await for I/O operations
- Follow RESTful API principles
- Document API endpoints

### Web Interface Guidelines
- Build responsive designs
- Use TailwindCSS for styling
- Implement proper loading states
- Handle errors gracefully
- Test across different browsers

## 🎯 Architecture Principles

### Mobile → Desktop Flow
1. Mobile apps capture and encode video
2. Stream to desktop via SRT/TCP protocols
3. Desktop processes and routes to broadcasting platforms
4. Web interface provides monitoring and controls

### Code Organization
- **Separation of Concerns:** Each component has a single responsibility
- **Modularity:** Code is organized into reusable modules
- **Documentation:** All public APIs are documented
- **Testing:** Comprehensive test coverage

## 🔄 Release Process

### Version Numbering
- Follow Semantic Versioning (SemVer)
- Format: `MAJOR.MINOR.PATCH`
- Mobile apps may have independent version numbers

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers incremented
- [ ] Release notes prepared

## 🚀 Deployment

### Mobile Apps
- **iOS:** App Store submission process
- **Android:** Google Play Store submission

### Desktop Platform
- Docker containerization
- Cloud deployment documentation
- Self-hosted installation guides

## 📞 Community

### Communication
- **GitHub Discussions:** General questions and ideas
- **GitHub Issues:** Bug reports and feature requests
- **Pull Requests:** Code contributions

### Code of Conduct
- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Maintain professionalism

## 📄 License

By contributing to Miktos Streamlab, you agree that your contributions will be licensed under the MIT License.

---

**Questions?** Open an issue or start a discussion on GitHub!