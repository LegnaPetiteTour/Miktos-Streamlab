#!/bin/bash

# Mobile Camera System - Quick Start Script
# Week 1 MVP - Complete Setup

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         Mobile Camera System - Quick Start Setup              ║"
echo "║                    Week 1 MVP Implementation                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if FFmpeg has SRT support
check_ffmpeg_srt() {
    print_status "Checking FFmpeg SRT support..."
    
    if ! command -v ffmpeg &> /dev/null; then
        print_error "FFmpeg not found!"
        echo ""
        echo "Please install FFmpeg with SRT support:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  brew install ffmpeg"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "  sudo apt install ffmpeg libsrt-dev"
        fi
        exit 1
    fi
    
    if ffmpeg -version | grep -q "libsrt"; then
        print_success "FFmpeg with SRT support found"
        return 0
    else
        print_error "FFmpeg found but SRT support missing"
        echo ""
        echo "Please install FFmpeg with SRT support:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  brew reinstall ffmpeg"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "  sudo apt install ffmpeg libsrt-dev"
        fi
        exit 1
    fi
}

# Check Python environment
check_python() {
    print_status "Checking Python environment..."
    
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found, creating..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    print_success "Python virtual environment activated"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    pip install -q --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt
        print_success "Python dependencies installed"
    fi
}

# Check Node.js for mobile app
check_node() {
    print_status "Checking Node.js for mobile app..."
    
    if ! command -v node &> /dev/null; then
        print_warning "Node.js not found (needed for mobile app)"
        echo "Install from: https://nodejs.org/"
        return 1
    fi
    
    print_success "Node.js found: $(node --version)"
    return 0
}

# Install mobile app dependencies
setup_mobile_app() {
    print_status "Setting up mobile app..."
    
    if [ -d "StreamLabCamera" ]; then
        cd StreamLabCamera
        
        if [ ! -d "node_modules" ]; then
            print_status "Installing mobile app dependencies..."
            npm install
            print_success "Mobile app dependencies installed"
        else
            print_success "Mobile app dependencies already installed"
        fi
        
        cd ..
    else
        print_warning "StreamLabCamera directory not found"
    fi
}

# Create quick test script
create_test_script() {
    print_status "Creating test script..."
    
    cat > test_mobile_camera.sh << 'EOF'
#!/bin/bash

# Test Mobile Camera System

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              Testing Mobile Camera System                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Activate Python environment
source venv/bin/activate

# Start SRT receiver
echo "Starting SRT receiver on port 9001..."
echo "Waiting for mobile camera connection..."
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m src.mobile.srt_receiver --port 9001 --mode window
EOF
    
    chmod +x test_mobile_camera.sh
    print_success "Test script created: ./test_mobile_camera.sh"
}

# Print instructions
print_instructions() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                      Setup Complete!                           ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📱 MOBILE APP SETUP:"
    echo "   1. Open StreamLabCamera/ in Xcode or Android Studio"
    echo "   2. Build and run on physical device (NOT simulator)"
    echo "   3. Grant camera permissions when prompted"
    echo ""
    echo "🖥️  DESKTOP RECEIVER SETUP:"
    echo "   1. Find your computer's local IP address:"
    echo "      • macOS: ifconfig | grep 'inet '"
    echo "      • Linux: ip addr show"
    echo "   2. Run the receiver:"
    echo "      $ ./test_mobile_camera.sh"
    echo ""
    echo "🎥 START STREAMING:"
    echo "   1. Enter your desktop IP in the mobile app"
    echo "   2. Tap 'START STREAMING'"
    echo "   3. Preview window should appear on desktop"
    echo ""
    echo "📊 EXPECTED RESULTS:"
    echo "   • Camera preview on phone: ✓"
    echo "   • Video recording starts: ✓"
    echo "   • Desktop receives stream: ⏳ (Week 1 implementation)"
    echo "   • Appears in OBS: ⏳ (Week 1 goal)"
    echo ""
    echo "🔧 TROUBLESHOOTING:"
    echo "   • No camera preview? → Check permissions"
    echo "   • Can't connect? → Verify desktop IP and same WiFi network"
    echo "   • High latency? → Check WiFi signal strength"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Test basic camera functionality"
    echo "   2. Verify desktop receiver works"
    echo "   3. Integrate with OBS"
    echo "   4. Measure end-to-end latency"
    echo ""
}

# Main execution
main() {
    echo ""
    print_status "Starting setup..."
    echo ""
    
    # Run checks and setup
    check_ffmpeg_srt
    check_python
    install_python_deps
    
    if check_node; then
        setup_mobile_app
    fi
    
    create_test_script
    print_instructions
}

# Run main function
main
