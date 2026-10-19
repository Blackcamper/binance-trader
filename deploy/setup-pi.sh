#!/bin/sh
# One-time setup on the Pi (run as user pi). Safe to run again.
set -eu
REPO=$HOME/binance-trader
KEY=$HOME/.ssh/pitrader_status
STATUS_URL=git@github.com:Blackcamper/pitrader-status.git

cd "$REPO"
for u in pitrader-sync.service pitrader-sync.timer; do sudo cp "deploy/$u" /etc/systemd/system/; done
sudo systemctl daemon-reload
sudo systemctl enable --now pitrader-sync.timer
echo "OK: hourly sync is on"

mkdir -p "$HOME/.ssh"
[ -f "$KEY" ] || ssh-keygen -q -t ed25519 -N "" -C "dronedk-pi status" -f "$KEY"
export GIT_SSH_COMMAND="ssh -i $KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
if [ ! -d "$HOME/pitrader-status/.git" ]; then
    if git clone -q "$STATUS_URL" "$HOME/pitrader-status" 2>/dev/null; then
        echo "OK: status repo cloned"
    else
        echo
        echo "NEXT: add this key as a deploy key WITH write access on"
        echo "github.com/Blackcamper/pitrader-status -> Settings -> Deploy keys -> Add deploy key"
        echo
        cat "$KEY.pub"
        echo
        echo "Then run: sh ~/binance-trader/deploy/setup-pi.sh"
        exit 0
    fi
fi
sh "$REPO/deploy/pi-sync.sh"
echo "OK: status published to pitrader-status"
