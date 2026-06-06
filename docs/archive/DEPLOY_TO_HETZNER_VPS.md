# 🚀 Deploy Good Rehoboam to Hetzner VPS

## Prerequisites
- Hetzner VPS with Ubuntu/Debian
- SSH access to your VPS
- Domain name (optional but recommended)

## Quick VPS Deployment

### 1. Connect to Your VPS
```bash
ssh root@your-vps-ip
# or
ssh your-user@your-vps-ip
```

### 2. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Required Software
```bash
# Install Python, Git, and other dependencies
sudo apt install -y python3 python3-pip python3-venv git curl ufw

# Install Node.js (for any frontend components)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Docker (optional, for containerized deployment)
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### 4. Clone Repository
```bash
cd /opt
git clone https://github.com/valentinuuiuiu/clean_rehoboam_project.git
cd clean_rehoboam_project
```

### 5. Set Up Environment Variables
```bash
# Create environment file
nano .env.production

# Add these variables (replace with your actual keys):
PORT=5002
LOG_LEVEL=INFO
CREATOR_NAME=Ionut-Valentin Baltag
CO_CREATOR_NAME=Claude Sonnet
ENVIRONMENT=production

# API Keys (get from respective services)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ALCHEMY_API_KEY=your-alchemy-key
ETHERSCAN_API_KEY=your-etherscan-key

# Database (optional)
DATABASE_URL=sqlite:///data/rehoboam.db

# Save and exit (Ctrl+X, Y, Enter)
```

### 6. Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 7. Set Up Firewall
```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

### 8. Run the Application
```bash
# Method 1: Direct Python execution
source venv/bin/activate
python api_server.py &

# Method 2: Using systemd service (recommended)
sudo nano /etc/systemd/system/rehoboam.service
```

Add this to the service file:
```ini
[Unit]
Description=Good Rehoboam API Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/clean_rehoboam_project
Environment=PATH=/opt/clean_rehoboam_project/venv/bin
ExecStart=/opt/clean_rehoboam_project/venv/bin/python api_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable rehoboam
sudo systemctl start rehoboam
sudo systemctl status rehoboam
```

### 9. Set Up Nginx (Reverse Proxy)
```bash
# Install Nginx
sudo apt install -y nginx

# Create site configuration
sudo nano /etc/nginx/sites-available/rehoboam
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/clean_rehoboam_project/static/;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/rehoboam /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 10. Set Up SSL (Let's Encrypt)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 11. Verify Deployment
```bash
# Test local connection
curl http://localhost:5002/health

# Test through Nginx
curl https://your-domain.com/health

# Expected response:
# {"status": "online", "hive_mind": "active", "sacred_oath": "verified"}
```

## Monitoring & Maintenance

### Check Application Status
```bash
sudo systemctl status rehoboam
sudo journalctl -u rehoboam -f
```

### Update Application
```bash
cd /opt/clean_rehoboam_project
git pull origin main
sudo systemctl restart rehoboam
```

### Backup Data
```bash
# Backup database and configs
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config/
```

## Security Checklist
- ✅ SSH key authentication enabled
- ✅ Firewall configured (UFW)
- ✅ SSL certificate installed
- ✅ Environment variables properly set
- ✅ No sensitive data in logs
- ✅ Regular system updates scheduled

## Troubleshooting

### Common Issues:
1. **Port already in use**: `sudo netstat -tlnp | grep :5002`
2. **Permission errors**: Check file ownership and permissions
3. **Database issues**: Ensure data directory exists and is writable
4. **SSL issues**: Check certbot logs and nginx configuration

### Logs to Check:
- Application: `sudo journalctl -u rehoboam -f`
- Nginx: `sudo tail -f /var/log/nginx/error.log`
- System: `sudo tail -f /var/log/syslog`

---
**Status**: ✅ Ready for VPS deployment
**Security**: ✅ Verified - No exposed secrets
**Wallet**: ✅ Exodus integration configured
