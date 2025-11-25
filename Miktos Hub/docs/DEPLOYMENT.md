# Deployment Guide

Production deployment options for Miktos Hub.

## Table of Contents

- [systemd Service (Linux)](#systemd-service-linux)
- [Docker Deployment](#docker-deployment)
- [Environment Variables](#environment-variables)
- [Reverse Proxy (nginx)](#reverse-proxy-nginx)
- [Security Considerations](#security-considerations)

---

## systemd Service (Linux)

### 1. Create Service File

Create `/etc/systemd/system/miktos-hub.service`:

```ini
[Unit]
Description=Miktos Hub - Live Streaming Orchestration Platform
After=network.target

[Service]
Type=simple
User=miktos
Group=miktos
WorkingDirectory=/opt/miktos-hub
Environment="PATH=/opt/miktos-hub/venv/bin"
ExecStart=/opt/miktos-hub/venv/bin/python main.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/miktos-hub/data

[Install]
WantedBy=multi-user.target

```

### 2. Setup Application

```bash

# Create user
sudo useradd -r -s /bin/false miktos

# Install application
sudo mkdir -p /opt/miktos-hub
sudo cp -r * /opt/miktos-hub/
sudo chown -R miktos:miktos /opt/miktos-hub

# Create virtual environment
cd /opt/miktos-hub
sudo -u miktos python -m venv venv
sudo -u miktos venv/bin/pip install -r requirements.txt

# Create data directory
sudo mkdir -p /opt/miktos-hub/data
sudo chown miktos:miktos /opt/miktos-hub/data

```

### 3. Configure

Edit `/opt/miktos-hub/config/settings.py`:

```python

# Production settings
database:
    url: "sqlite:////opt/miktos-hub/data/miktos_hub.db"

logging:
    level: "INFO"
    file: "/var/log/miktos-hub/app.log"

```

### 4. Start Service

```bash

# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable miktos-hub

# Start service
sudo systemctl start miktos-hub

# Check status
sudo systemctl status miktos-hub

# View logs
sudo journalctl -u miktos-hub -f

```

### 5. Manage Service

```bash

# Stop
sudo systemctl stop miktos-hub

# Restart
sudo systemctl restart miktos-hub

# Disable auto-start
sudo systemctl disable miktos-hub

```

---

## Docker Deployment

### 1. Create Dockerfile

`Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]

```

### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  miktos-hub:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - OBS_HOST=host.docker.internal
      - OBS_PORT=4455
      - OBS_PASSWORD=${OBS_PASSWORD}
    restart: unless-stopped
    networks:
      - miktos-network

  # Optional: nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - miktos-hub
    networks:
      - miktos-network

networks:
  miktos-network:
    driver: bridge

```

### 3. Build and Run

```bash

# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f miktos-hub

# Stop services
docker-compose down

```

---

## Environment Variables

Create `.env` file:

```bash

# OBS Configuration
OBS_HOST=localhost
OBS_PORT=4455
OBS_PASSWORD=your-password-here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///data/miktos_hub.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/miktos-hub/app.log

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,your-domain.com

```

Load in application:

```python
import os
from dotenv import load_dotenv

load_dotenv()

obs_host = os.getenv('OBS_HOST', 'localhost')
obs_port = int(os.getenv('OBS_PORT', 4455))

```

---

## Reverse Proxy (nginx)

### nginx Configuration

`/etc/nginx/sites-available/miktos-hub`:

```nginx
upstream miktos_hub {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://miktos_hub;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://miktos_hub;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files (if any)
    location /static {
        alias /opt/miktos-hub/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/miktos-hub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

```

---

## Security Considerations

### 1. Firewall Configuration

```bash

# UFW (Ubuntu)
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

```

### 2. SSL/TLS Certificates

```bash

# Let's Encrypt with certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

```

### 3. Application Security

- **Change default passwords**

- **Use environment variables for secrets**

- **Enable CORS only for trusted domains**

- **Implement rate limiting**

- **Regular security updates**

```python

# config/settings.py
security:
    allowed_hosts: ["your-domain.com", "localhost"]
    cors_origins: ["https://your-frontend.com"]
    rate_limit: "100/hour"

```

### 4. Backup Strategy

```bash

#!/bin/bash
# backup.sh - Daily database backup

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/miktos-hub"
mkdir -p "$BACKUP_DIR"

# Backup database
cp /opt/miktos-hub/data/miktos_hub.db "$BACKUP_DIR/miktos_hub_${DATE}.db"

# Compress old backups
find "$BACKUP_DIR" -name "*.db" -mtime +7 -exec gzip {} \;

# Remove backups older than 30 days
find "$BACKUP_DIR" -name "*.db.gz" -mtime +30 -delete

```

Add to crontab:

```bash
0 2 * * * /opt/miktos-hub/backup.sh

```

---

## Monitoring

### systemd Status

```bash

# Service status
systemctl status miktos-hub

# Recent logs
journalctl -u miktos-hub -n 100

# Follow logs
journalctl -u miktos-hub -f

```

### Health Check Endpoint

```bash

# Check application health
curl http://localhost:8000/api/health

# Setup monitoring
watch -n 5 'curl -s http://localhost:8000/api/health | jq .'

```

### Log Rotation

`/etc/logrotate.d/miktos-hub`:

```text
/var/log/miktos-hub/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 miktos miktos
    sharedscripts
    postrotate
        systemctl reload miktos-hub
    endscript
}

```

---

## Troubleshooting

### Service Won't Start

```bash

# Check logs
sudo journalctl -u miktos-hub -n 50

# Check permissions
ls -la /opt/miktos-hub/data

# Verify Python environment
/opt/miktos-hub/venv/bin/python --version

```

### High Memory Usage

```bash

# Monitor resources
htop
systemctl status miktos-hub

# Adjust service limits in systemd
[Service]
MemoryLimit=512M
CPUQuota=50%

```

### Database Locked

```bash

# Check for stale locks
fuser /opt/miktos-hub/data/miktos_hub.db

# Kill if necessary
fuser -k /opt/miktos-hub/data/miktos_hub.db

```

---

## Production Checklist

- [ ] Change all default passwords
- [ ] Configure SSL/TLS certificates
- [ ] Setup firewall rules
- [ ] Enable systemd service
- [ ] Configure log rotation
- [ ] Setup automated backups
- [ ] Configure monitoring/alerts
- [ ] Test disaster recovery
- [ ] Document deployment process
- [ ] Review security settings
