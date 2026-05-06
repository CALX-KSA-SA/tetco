#!/usr/bin/env bash
# One-shot deploy script for the tetco GitHub Pages update.
#
# Usage:  bash push.sh
# When prompted for the password, paste your GitHub PAT (the one you
# generated AFTER rotating the previous exposed token).

set -euo pipefail

REPO_URL="https://github.com/calx-ksa-sa/tetco.git"
WORK_DIR="$(mktemp -d -t tetco-deploy-XXXXXX)"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ">>> Cloning $REPO_URL into $WORK_DIR ..."
git clone "$REPO_URL" "$WORK_DIR"
cd "$WORK_DIR"

echo ">>> Copying updated files from $SRC_DIR ..."
cp "$SRC_DIR/index.html"           ./index.html
cp "$SRC_DIR/universities.sqlite"  ./universities.sqlite

echo ">>> Staging changes ..."
git add index.html universities.sqlite
git status --short

if git diff --cached --quiet; then
  echo "Nothing to commit — repo already matches local files."
  exit 0
fi

echo ">>> Committing ..."
git commit -m "Remove Excel-import label; load universities from SQLite via sql.js"

echo ">>> Pushing — git will ask for your username and PAT now."
git push origin HEAD

echo ""
echo "✅ Done. Wait ~1 minute, then check:"
echo "   https://calx-ksa-sa.github.io/tetco/"
echo ""
echo "Open DevTools console — you should see:"
echo "   [RDO] Loaded 48 universities from SQLite"
