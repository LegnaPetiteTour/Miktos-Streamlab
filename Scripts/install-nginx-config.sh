#!/bin/bash
# Simple NGINX installation - Run each step manually
# ====================================================

echo "🚀 NGINX RTMP Configuration Installation"
echo ""
echo "These commands will ask for your Mac password (the one you use to login)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Backup existing nginx config"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo cp /opt/homebrew/etc/nginx/nginx.conf /opt/homebrew/etc/nginx/nginx.conf.backup

if [ $? -eq 0 ]; then
    echo "✅ Backup created"
else
    echo "❌ Backup failed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Install new configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo cp /tmp/nginx-configured.conf /opt/homebrew/etc/nginx/nginx.conf

if [ $? -eq 0 ]; then
    echo "✅ Configuration installed"
else
    echo "❌ Installation failed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Test configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

/opt/homebrew/opt/nginx-full/bin/nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Configuration is valid"
else
    echo "❌ Configuration test failed"
    echo "Restoring backup..."
    sudo cp /opt/homebrew/etc/nginx/nginx.conf.backup /opt/homebrew/etc/nginx/nginx.conf
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Start NGINX"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo brew services start denji/nginx/nginx-full

sleep 2

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Verify NGINX is running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if lsof -i :1935 > /dev/null 2>&1; then
    echo "✅ NGINX RTMP server is running on port 1935"
else
    echo "❌ NGINX not running on port 1935"
    echo "Check logs: tail -f /opt/homebrew/var/log/nginx/error.log"
    exit 1
fi

if lsof -i :8080 > /dev/null 2>&1; then
    echo "✅ NGINX stats server is running on port 8080"
else
    echo "⚠️  Stats server not on port 8080 (this is optional)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SUCCESS! NGINX RTMP is ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📡 RTMP Server: rtmp://localhost:1935/live"
echo "📊 Stats Page:  http://localhost:8080/stat"
echo ""
echo "🎬 Next: Configure OBS Studio"
echo "   Settings → Stream → Custom"
echo "   Server: rtmp://localhost/live"
echo "   Stream Key: streamlab"
echo ""
echo "Ready to stream to YouTube EN and FR! 🚀"
