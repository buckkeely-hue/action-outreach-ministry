#!/bin/bash
# Auto-deploy Action Outreach Ministry.
# When origin/main advances, update the working tree and restart the service.
# Only tracked SOURCE files change — ignored data (users, content, uploads, donor
# PII) is never touched, so live data and uploaded images are always preserved.
set -euo pipefail

export HOME=/root                    # systemd runs services with no HOME; git needs one
REPO="/var/www/action-outreach-ministry"
BRANCH="main"
cd "$REPO"

# -c safe.directory avoids git's "dubious ownership" abort when root operates on the
# www-data-owned repo (does not depend on any global/user gitconfig being present).
GIT="git -c safe.directory=$REPO"

$GIT fetch --quiet origin "$BRANCH"
LOCAL="$($GIT rev-parse HEAD)"
REMOTE="$($GIT rev-parse "origin/$BRANCH")"

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "$(date '+%F %T') [auto-deploy] $LOCAL -> $REMOTE"
  $GIT reset --hard "origin/$BRANCH"
  chown -R www-data:www-data "$REPO"
  systemctl restart aom
  echo "$(date '+%F %T') [auto-deploy] pulled and restarted aom"
else
  echo "$(date '+%F %T') [auto-deploy] already up to date"
fi
