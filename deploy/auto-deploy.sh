#!/bin/bash
# Auto-deploy Action Outreach Ministry.
# When origin/main advances, update the working tree and restart the service.
# Only tracked SOURCE files change — ignored data (users, content, uploads, donor
# PII) is never touched, so live data and uploaded images are always preserved.
set -euo pipefail

REPO="/var/www/action-outreach-ministry"
BRANCH="main"
cd "$REPO"

git fetch --quiet origin "$BRANCH"
LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse "origin/$BRANCH")"

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "$(date '+%F %T') [auto-deploy] $LOCAL -> $REMOTE"
  git reset --hard "origin/$BRANCH"
  chown -R www-data:www-data "$REPO"
  systemctl restart aom
  echo "$(date '+%F %T') [auto-deploy] pulled and restarted aom"
else
  echo "$(date '+%F %T') [auto-deploy] already up to date"
fi
