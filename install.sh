#!/usr/bin/env bash
# quran-cli one-line installer
# Usage: curl -fsSL https://raw.githubusercontent.com/zaryif/quran-cli/main/install.sh | bash
set -e

echo ""
echo "  بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ"
echo "  Installing quran-cli..."
echo ""

REPO="https://github.com/zaryif/quran-cli.git"

# Detect pip command (prefer pip3 for macOS compatibility)
if command -v pip3 &>/dev/null; then
  PIP=pip3
elif command -v pip &>/dev/null; then
  PIP=pip
else
  echo "  ✗ pip not found. Install Python 3.11+ first."
  echo ""
  echo "    macOS:   brew install python3"
  echo "    Linux:   sudo apt install python3-pip"
  echo "    Windows: python.org/downloads"
  exit 1
fi

# Check Python version
PYVER=$($PIP --version 2>/dev/null | grep -oP 'python \K[0-9]+\.[0-9]+' || echo "3.0")
echo "  Using: $PIP (Python $PYVER)"

# Install from GitHub
echo "  Installing from GitHub..."
$PIP install "git+${REPO}" --break-system-packages 2>/dev/null \
  || $PIP install "git+${REPO}" 2>/dev/null \
  || {
    echo ""
    echo "  ✗ pip install failed. Try in a virtual environment:"
    echo ""
    echo "    python3 -m venv ~/.quran-venv"
    echo "    source ~/.quran-venv/bin/activate"
    echo "    pip install git+${REPO}"
    exit 1
  }

echo ""
echo "  ✓ quran-cli installed successfully!"
echo ""
echo "  Run:  quran              — interactive dashboard"
echo "        quran schedule     — full day prayer schedule"
echo "        quran clock        — live prayer clock"
echo "        quran --help       — all commands"
echo ""
