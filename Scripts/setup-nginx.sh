#!/bin/bash
# Setup NGINX RTMP for Miktos StreamLab
# ======================================

set -e

echo "🚀 Setting up NGINX RTMP for dual-path streaming..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if nginx-rtmp.conf exists
if [ ! -f "nginx-rtmp.conf" ]; then
    echo -e "${RED}❌ nginx-rtmp.conf not found in current directory${NC}"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}📝 IMPORTANT: Edit .env and add your YouTube stream keys:${NC}"
    echo "   - YOUTUBE_EN_STREAM_KEY"
    echo "   - YOUTUBE_FR_STREAM_KEY"
    echo ""
    read -p "Press Enter to open .env for editing..."
    ${EDITOR:-nano} .env
fi

# Read stream keys from .env
echo "📖 Reading stream keys from .env..."
if [ -f ".env" ]; then
    source .env
    
    if [ -z "$YOUTUBE_EN_STREAM_KEY" ] || [ "$YOUTUBE_EN_STREAM_KEY" = "your_youtube_en_stream_key_here" ]; then
        echo -e "${RED}❌ YOUTUBE_EN_STREAM_KEY not set in .env${NC}"
        echo "   Get it from: https://studio.youtube.com -> Go Live -> Stream Key"
        exit 1
    fi
    
    if [ -z "$YOUTUBE_FR_STREAM_KEY" ] || [ "$YOUTUBE_FR_STREAM_KEY" = "your_youtube_fr_stream_key_here" ]; then
        echo -e "${YELLOW}⚠️  YOUTUBE_FR_STREAM_KEY not set in .env${NC}"
        echo "   Continuing with EN channel only..."
    fi
    
    echo -e "${GREEN}✅ Stream keys loaded${NC}"
else
    echo -e "${RED}❌ Could not read .env file${NC}"
    exit 1
fi

# Create nginx config with actual keys
echo "🔧 Creating nginx configuration with your stream keys..."
NGINX_CONF="/tmp/nginx-rtmp-configured.conf"
cp nginx-rtmp.conf "$NGINX_CONF"

# Replace placeholders with actual keys
sed -i '' "s/YOUR_EN_STREAM_KEY/$YOUTUBE_EN_STREAM_KEY/g" "$NGINX_CONF"

if [ ! -z "$YOUTUBE_FR_STREAM_KEY" ] && [ "$YOUTUBE_FR_STREAM_KEY" != "your_youtube_fr_stream_key_here" ]; then
    sed -i '' "s/YOUR_FR_STREAM_KEY/$YOUTUBE_FR_STREAM_KEY/g" "$NGINX_CONF"
else
    # Comment out FR stream if not configured
    sed -i '' '/YOUR_FR_STREAM_KEY/s/^/# DISABLED: /' "$NGINX_CONF"
fi

echo -e "${GREEN}✅ Configuration prepared${NC}"

# Backup existing nginx config
echo "💾 Backing up existing nginx configuration..."
if [ -f "/opt/homebrew/etc/nginx/nginx.conf" ]; then
    sudo cp /opt/homebrew/etc/nginx/nginx.conf /opt/homebrew/etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backup created${NC}"
fi

# Copy new configuration
echo "📝 Installing new nginx configuration..."
sudo cp "$NGINX_CONF" /opt/homebrew/etc/nginx/nginx.conf
echo -e "${GREEN}✅ Configuration installed${NC}"

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if /opt/homebrew/opt/nginx-full/bin/nginx -t; then
    echo -e "${GREEN}✅ Configuration is valid${NC}"
else
    echo -e "${RED}❌ Configuration test failed${NC}"
    echo "   Restoring backup..."
    sudo cp /opt/homebrew/etc/nginx/nginx.conf.backup.* /opt/homebrew/etc/nginx/nginx.conf 2>/dev/null || true
    exit 1
fi

# Check if nginx is already running
if pgrep -x nginx > /dev/null; then
    echo "🔄 Reloading nginx..."
    /opt/homebrew/opt/nginx-full/bin/nginx -s reload
    echo -e "${GREEN}✅ NGINX reloaded${NC}"
else
    echo "🚀 Starting nginx..."
    sudo brew services start denji/nginx/nginx-full
    sleep 2
    echo -e "${GREEN}✅ NGINX started${NC}"
fi

# Verify nginx is running
echo ""
echo "🔍 Verifying nginx is running..."
if lsof -i :1935 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ NGINX RTMP server listening on port 1935${NC}"
else
    echo -e "${RED}❌ NGINX not listening on port 1935${NC}"
    echo "   Check logs: tail -f /opt/homebrew/var/log/nginx/error.log"
    exit 1
fi

if lsof -i :8080 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ NGINX stats server listening on port 8080${NC}"
else
    echo -e "${YELLOW}⚠️  Stats server not listening on port 8080${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 NGINX RTMP Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📡 RTMP Server: rtmp://localhost:1935/live"
echo "📊 Stats Page:  http://localhost:8080/stat"
echo "📝 Logs:        /opt/homebrew/var/log/nginx/error.log"
echo ""
echo "🎬 OBS Configuration:"
echo "   1. Settings → Stream"
echo "   2. Service: Custom"
echo "   3. Server: rtmp://localhost/live"
echo "   4. Stream Key: streamlab (or any name)"
echo ""
echo "📺 YouTube Channels Configured:"
echo "   ✅ English Channel: ${YOUTUBE_EN_STREAM_KEY:0:4}-****-****-****"
if [ ! -z "$YOUTUBE_FR_STREAM_KEY" ] && [ "$YOUTUBE_FR_STREAM_KEY" != "your_youtube_fr_stream_key_here" ]; then
    echo "   ✅ French Channel:  ${YOUTUBE_FR_STREAM_KEY:0:4}-****-****-****"
else
    echo "   ⚠️  French Channel: Not configured"
fi
echo ""
echo "🧪 Test Stream:"
echo "   1. Open OBS Studio"
echo "   2. Click 'Start Streaming'"
echo "   3. Check stats: open http://localhost:8080/stat"
echo "   4. Check YouTube Studio for both channels"
echo ""
echo -e "${GREEN}Ready to stream! 🎥${NC}"
