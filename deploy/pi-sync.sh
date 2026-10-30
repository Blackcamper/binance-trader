#!/bin/sh
# Hourly job on the Pi (pitrader-sync.timer), approved by Jakob 2026-10-19:
#  1. pull new code from the pi-live branch (public repo, no key); restart only if it changed
#     and the new code compiles
#  2. push the latest status files to the private status repo (deploy key for that repo only)
# Nothing here touches money or exchange keys.
set -u
REPO=$HOME/binance-trader
STATUS=$HOME/pitrader-status
BRANCH=pi-live
KEY=$HOME/.ssh/pitrader_status
DATA=$REPO/data/sim-v2
UNITS="pitrader.service pitrader-llm.service pitrader-llm.timer pitrader-sync.service pitrader-sync.timer pitrader-stocks.service pitrader-stocks.timer"
STOCKS=$REPO/data/stocks-v1

cd "$REPO" || exit 1
if git fetch -q origin "$BRANCH"; then
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse "origin/$BRANCH")" ]; then
        old=$(git rev-parse HEAD)
        git checkout -q -B "$BRANCH" "origin/$BRANCH"
        if python3 -m compileall -q pitrader; then
            for u in $UNITS; do sudo cp "deploy/$u" /etc/systemd/system/; done
            sudo systemctl daemon-reload
            sudo systemctl restart pitrader
            echo "updated $old -> $(git rev-parse HEAD)"
        else
            git checkout -q -B "$BRANCH" "$old"      # broken code never goes live
            echo "update rejected: code does not compile"
        fi
    fi
fi

# stocks timer (added 2026-10-30): installed here, outside the update step, because the
# copy of this script that pulls the update is still the old one
if [ -f deploy/pitrader-stocks.timer ] && ! systemctl is-enabled -q pitrader-stocks.timer 2>/dev/null; then
    for u in pitrader-stocks.service pitrader-stocks.timer; do sudo cp "deploy/$u" /etc/systemd/system/; done
    sudo systemctl daemon-reload
    sudo systemctl enable --now pitrader-stocks.timer && echo "stocks timer enabled"
fi

[ -f "$KEY" ] && [ -d "$STATUS/.git" ] || exit 0
export GIT_SSH_COMMAND="ssh -i $KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
cd "$STATUS" || exit 0
git pull -q --rebase origin main 2>/dev/null
for f in status.json summary.txt llm-summary.json; do
    [ -f "$DATA/$f" ] && cp "$DATA/$f" "$STATUS/$f"
done
if [ -f "$DATA/equity.csv" ]; then
    { head -1 "$DATA/equity.csv"; tail -n 300 "$DATA/equity.csv" | grep -v '^utc'; } > "$STATUS/equity-tail.csv"
fi
[ -f "$DATA/backtest/report.md" ] && cp "$DATA/backtest/report.md" "$STATUS/backtest.md"
mkdir -p "$STATUS/stocks"
for f in status.json summary.txt; do
    [ -f "$STOCKS/$f" ] && cp "$STOCKS/$f" "$STATUS/stocks/$f"
done
if [ -f "$STOCKS/equity.csv" ]; then
    { head -1 "$STOCKS/equity.csv"; tail -n 120 "$STOCKS/equity.csv" | grep -v '^date'; } > "$STATUS/stocks/equity-tail.csv"
fi
[ -f "$STOCKS/backtest/report.md" ] && cp "$STOCKS/backtest/report.md" "$STATUS/stocks/backtest.md"
git add -A
git -c user.name=dronedk-pi -c user.email=pi@dronedk-pi commit -qm "status $(date -u +%Y-%m-%dT%H:%MZ)" \
    && git push -q origin HEAD:main
exit 0
