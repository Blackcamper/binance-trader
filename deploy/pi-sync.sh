#!/bin/sh
# Hourly job on the Pi (pitrader-sync.timer), approved by Jakob 2026-10-19:
#  1. pull new code from the pi-live branch (public repo, no key); restart only if it changed
#     and the new code compiles
#  2. copy the Haiku news diary (public branch nyheds-dagbog, written by a scheduled Claude task)
#     and score it with public daily prices; paper only, added 2026-10-20
#  3. push the latest status files to the private status repo (deploy key for that repo only)
# Nothing here touches money or exchange keys.
set -u
REPO=$HOME/binance-trader
STATUS=$HOME/pitrader-status
BRANCH=pi-live
KEY=$HOME/.ssh/pitrader_status
DATA=$REPO/data/sim-v2
UNITS="pitrader.service pitrader-llm.service pitrader-llm.timer pitrader-sync.service pitrader-sync.timer"

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

NEWS=$REPO/data/nyheder
if git fetch -q origin nyheds-dagbog 2>/dev/null; then
    mkdir -p "$NEWS/journal"
    git archive origin/nyheds-dagbog journal 2>/dev/null | tar -x -C "$NEWS" 2>/dev/null
    timeout 900 nice -n 15 python3 -m pitrader news-score >/dev/null 2>&1
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
[ -f "$NEWS/score.md" ] && cp "$NEWS/score.md" "$STATUS/nyheder.md"
git add -A
git -c user.name=dronedk-pi -c user.email=pi@dronedk-pi commit -qm "status $(date -u +%Y-%m-%dT%H:%MZ)" \
    && git push -q origin HEAD:main
exit 0
