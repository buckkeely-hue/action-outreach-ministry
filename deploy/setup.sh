#!/bin/bash
# Action Outreach Ministry — one-time VPS setup (Ubuntu 22.04, run as root)
set -e

echo "=== Installing packages ==="
apt-get update -qq
apt-get install -y nginx python3 certbot python3-certbot-nginx git ufw

echo "=== Configuring firewall ==="
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "=== Cloning repository ==="
git clone https://github.com/buckkeely-hue/action-outreach-ministry.git /var/www/action-outreach-ministry
cd /var/www/action-outreach-ministry

echo "=== Creating data files ==="
echo '{}' > ministry_users.json
echo '{}' > ministry_sessions.json
echo '[]' > ministry_transactions.json
chown -R www-data:www-data /var/www/action-outreach-ministry
chmod 600 ministry_users.json ministry_sessions.json ministry_transactions.json

echo "=== Installing systemd service ==="
cp deploy/aom.service /etc/systemd/system/aom.service
systemctl daemon-reload
systemctl enable aom
systemctl start aom

echo "=== Configuring nginx ==="
cp deploy/nginx.conf /etc/nginx/sites-available/aom
ln -sf /etc/nginx/sites-available/aom /etc/nginx/sites-enabled/aom
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "=== Obtaining SSL certificate ==="
certbot --nginx -d actionoutreachministry.com -d www.actionoutreachministry.com --non-interactive --agree-tos -m admin@actionoutreachministry.com

echo ""
echo "=== Setup complete! ==="
echo "Site:       https://actionoutreachministry.com"
echo "Admin:      https://actionoutreachministry.com  → Admin button → login: admin / Ministrey2025"
echo "Service:    systemctl status aom"
echo "Logs:       journalctl -u aom -f"
echo "Update:     cd /var/www/action-outreach-ministry && git pull && systemctl restart aom"
