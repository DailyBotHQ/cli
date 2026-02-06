#!/usr/bin/env bash
# DailyBot CLI installer
# Usage: curl -sSL https://cli.dailybot.com/install.sh | bash

set -euo pipefail

PACKAGE="dailybot-cli"
MIN_PYTHON="3.9"

echo "Installing DailyBot CLI..."

# Check for Python 3
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        if [ -n "$version" ]; then
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
                PYTHON="$cmd"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python >= $MIN_PYTHON is required but not found."
    echo "Install Python from https://www.python.org/downloads/"
    exit 1
fi

echo "Using $PYTHON ($($PYTHON --version 2>&1))"

# Install via pip
if $PYTHON -m pip install --upgrade "$PACKAGE" 2>/dev/null; then
    echo ""
    echo "DailyBot CLI installed successfully!"
    echo ""
    echo "Get started:"
    echo "  dailybot auth login"
    echo "  dailybot --help"
else
    echo ""
    echo "pip install failed. Trying with --user flag..."
    $PYTHON -m pip install --user --upgrade "$PACKAGE"
    echo ""
    echo "DailyBot CLI installed (user install)."
    echo "Make sure ~/.local/bin is in your PATH."
    echo ""
    echo "Get started:"
    echo "  dailybot auth login"
    echo "  dailybot --help"
fi
