#!/usr/bin/env bash
# quran-cli one-line installer
set -e
echo "Installing quran-cli..."

# macOS ships 'python' as Python 2 — always prefer pip3/python3
if command -v pip3 &>/dev/null; then
  pip3 install quran-cli
elif command -v pip &>/dev/null; then
  pip install quran-cli
else
  echo "Error: pip not found. Install Python 3.11+ first."
  echo "  macOS:  brew install python3"
  echo "  Linux:  sudo apt install python3-pip"
  exit 1
fi

echo ""
echo "✓ Done. Run: quran schedule"
