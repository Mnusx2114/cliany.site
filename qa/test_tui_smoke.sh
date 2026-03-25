#!/usr/bin/env bash
set -e



PASS=0
FAIL=0

echo "=== Testing TUI ==="

if uv run python -c "from cliany_site.tui.app import CliAnySiteApp"; then
    echo "✅ IMPORT PASS"
    PASS=$((PASS + 1))
else
    echo "❌ IMPORT FAIL"
    FAIL=$((FAIL + 1))
fi

if uv run cliany-site --help | grep -q "tui"; then
    echo "✅ CLI REGISTRATION PASS"
    PASS=$((PASS + 1))
else
    echo "❌ CLI REGISTRATION FAIL"
    FAIL=$((FAIL + 1))
fi

echo "---"
echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [ $FAIL -gt 0 ]; then
    exit 1
fi
