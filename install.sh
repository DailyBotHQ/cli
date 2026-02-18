#!/usr/bin/env bash
# DailyBot CLI installer
# Usage: curl -sSL https://cli.dailybot.com/install.sh | bash
#
# Installs the dailybot-cli package using the best available method:
#   1. pipx   (isolated environment, recommended)
#   2. uv     (isolated environment, fast)
#   3. pip    (if already inside a virtualenv)
#   4. pip --user (last resort)

set -euo pipefail

PACKAGE="dailybot-cli"
COMMAND="dailybot"
MIN_PYTHON="3.9"

# --- Helpers ---

has() { command -v "$1" &>/dev/null; }

info()    { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
success() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn()    { printf '\033[1;33m==>\033[0m %s\n' "$*" >&2; }
error()   { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; }

in_virtualenv() {
    "$PYTHON" -c "import sys; sys.exit(0 if (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)) else 1)" 2>/dev/null
}

# --- Find Python >= 3.9 ---

PYTHON=""
for cmd in python3 python; do
    if has "$cmd"; then
        ok=$("$cmd" -c "
import sys
v = sys.version_info
print('yes' if v >= (3, 9) else 'no')
" 2>/dev/null || echo "no")
        if [ "$ok" = "yes" ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    error "Python >= $MIN_PYTHON is required but not found."
    echo "  Install Python from https://www.python.org/downloads/"
    exit 1
fi

info "Found $($PYTHON --version 2>&1)"

# --- Install ---

installed=false

# 1. pipx (preferred — isolated env, manages PATH)
if ! $installed && has pipx; then
    info "Installing with pipx..."
    if pipx install "$PACKAGE" --force 2>&1; then
        installed=true
    else
        warn "pipx install failed, trying next method..."
    fi
fi

# 2. uv tool (same benefits as pipx)
if ! $installed && has uv; then
    info "Installing with uv..."
    if uv tool install "$PACKAGE" --force 2>&1; then
        installed=true
    else
        warn "uv install failed, trying next method..."
    fi
fi

# 3. pip inside an active virtualenv (safe, no system pollution)
if ! $installed && in_virtualenv; then
    info "Virtualenv detected, installing with pip..."
    if $PYTHON -m pip install --upgrade "$PACKAGE" 2>&1; then
        installed=true
    else
        warn "pip install failed inside virtualenv."
    fi
fi

# 4. pip (system or --user fallback)
if ! $installed; then
    if ! $PYTHON -m pip --version &>/dev/null; then
        error "No suitable installer found."
        echo ""
        echo "  Install one of the following, then re-run this script:"
        echo "    pipx  - https://pipx.pypa.io/stable/installation/"
        echo "    uv    - https://docs.astral.sh/uv/getting-started/installation/"
        echo "    pip   - $PYTHON -m ensurepip --upgrade"
        exit 1
    fi

    info "Installing with pip..."
    if $PYTHON -m pip install --upgrade "$PACKAGE" 2>&1; then
        installed=true
    else
        warn "System pip install failed, trying --user install..."
        if $PYTHON -m pip install --user --upgrade "$PACKAGE" 2>&1; then
            installed=true

            # Check if ~/.local/bin is in PATH
            user_bin="$($PYTHON -c "import site; print(site.getusersitepackages().replace('/lib/python', '/bin').split('/lib/')[0] + '/bin')" 2>/dev/null || echo "$HOME/.local/bin")"
            case ":$PATH:" in
                *":$user_bin:"*) ;;
                *)
                    warn "$user_bin is not in your PATH."
                    echo ""
                    echo "  Add it by running:"
                    echo "    export PATH=\"$user_bin:\$PATH\""
                    echo ""
                    echo "  To make it permanent, add that line to your ~/.bashrc or ~/.zshrc"
                    ;;
            esac
        fi
    fi
fi

if ! $installed; then
    error "All installation methods failed."
    echo ""
    echo "  You can try manually:"
    echo "    pipx install $PACKAGE"
    echo "    # or"
    echo "    pip install $PACKAGE"
    exit 1
fi

# --- Verify ---

echo ""
if has "$COMMAND"; then
    success "DailyBot CLI installed successfully! ($($COMMAND --version 2>&1))"
else
    success "DailyBot CLI installed successfully!"
    warn "The '$COMMAND' command is not on your PATH yet."
    echo "  You may need to restart your terminal or add the install directory to PATH."
fi

echo ""
echo "  Get started:"
echo "    dailybot login"
echo "    dailybot --help"
echo ""
