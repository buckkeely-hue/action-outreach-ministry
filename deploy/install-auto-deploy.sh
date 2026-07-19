#!/bin/bash
# One-time installer for Action Outreach Ministry auto-deploy.
# Run ONCE on the VPS as root:
#   cd /var/www/action-outreach-ministry && sudo bash deploy/install-auto-deploy.sh
#
# After this, every push to GitHub main goes live automatically within ~2 minutes.
set -euo pipefail

REPO="/var/www/action-outreach-ministry"

# Allow git to operate on the www-data-owned repo without a "dubious ownership" error.
# Use --system so it applies even under systemd (which runs services with no HOME/user gitconfig).
git config --system --add safe.directory "$REPO" || true
git config --global --add safe.directory "$REPO" || true

chmod +x "$REPO/deploy/auto-deploy.sh"
cp "$REPO/deploy/aom-deploy.service" /etc/systemd/system/aom-deploy.service
cp "$REPO/deploy/aom-deploy.timer"   /etc/systemd/system/aom-deploy.timer
systemctl daemon-reload
systemctl enable --now aom-deploy.timer

echo "Timer installed. Applying current code and restarting once..."
chown -R www-data:www-data "$REPO"
systemctl restart aom
"$REPO/deploy/auto-deploy.sh"

echo
systemctl list-timers aom-deploy.timer --no-pager || true
echo
echo "Done. Future pushes to main go live within ~2 minutes."
echo "  Watch deploys:  journalctl -u aom-deploy.service -f"
