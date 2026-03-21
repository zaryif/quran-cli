#!/usr/bin/env bash
# quran-cli 1-click automated installer for macOS / Linux

set -e

LOG_FILE="quran_install_error.log"

echo "🕌 Installing quran-cli..."

# Catch errors and log them
exec 2> >(tee -a "$LOG_FILE" >&2)

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is required but not installed." | tee -a "$LOG_FILE"
    echo "Please install Python 3.10+ to continue."
    exit 1
fi

echo "-> Fetching latest version from GitHub via pip..."
python3 -m pip install git+https://github.com/zaryif/quran-cli.git

# Auto-fix PATH issue
LOCAL_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    echo "-> Fixing PATH variable..."
    if [ -n "$ZSH_VERSION" ] || [[ "$SHELL" == *"zsh"* ]]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.zshrc 2>/dev/null; then
            echo '\nexport PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        fi
        echo "⚠️  IMPORTANT: Run 'source ~/.zshrc' or restart your terminal before typing 'quran'."
    elif [ -n "$BASH_VERSION" ] || [[ "$SHELL" == *"bash"* ]]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc 2>/dev/null; then
            echo '\nexport PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        fi
        echo "⚠️  IMPORTANT: Run 'source ~/.bashrc' or restart your terminal before typing 'quran'."
    else
        echo "⚠️  IMPORTANT: Please add $LOCAL_BIN to your PATH manually."
    fi
else
    echo "-> PATH is already configured correctly."
fi

# Clean up empty error logs
if [ ! -s "$LOG_FILE" ]; then
    rm -f "$LOG_FILE"
fi

echo ""
echo "✅ quran-cli installed successfully!"
echo "Type 'quran' to launch the interactive dashboard."
