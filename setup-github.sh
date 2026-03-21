#!/usr/bin/env bash
# ============================================================
#  quran-cli — GitHub Repository Setup Script
#  Run this on YOUR machine after extracting the zip.
#  Creates the GitHub repo and pushes everything in one go.
# ============================================================

set -e

REPO_NAME="quran-cli"
GITHUB_USER=""          # ← fill in your GitHub username
DESCRIPTION="An Islamic terminal companion — prayer times, Quran reading, Ramadan schedule, Eid guide, AI Hadith guide, and cross-device notifications. Built for Muslim developers."

# ── 1. Check dependencies ──────────────────────────────────
if ! command -v gh &>/dev/null; then
  echo "Install GitHub CLI first: https://cli.github.com"
  echo "  macOS:  brew install gh"
  echo "  Ubuntu: sudo apt install gh"
  exit 1
fi

if ! command -v git &>/dev/null; then
  echo "git not found. Please install git."
  exit 1
fi

# ── 2. Authenticate with GitHub ────────────────────────────
echo "→ Checking GitHub authentication..."
if ! gh auth status &>/dev/null; then
  echo "→ Logging in to GitHub..."
  gh auth login
fi

# ── 3. Create the remote repository ────────────────────────
echo "→ Creating GitHub repository: $REPO_NAME"
gh repo create "$REPO_NAME" \
  --public \
  --description "$DESCRIPTION" \
  --homepage "https://github.com/$GITHUB_USER/$REPO_NAME" \
  --no-clone

# ── 4. Add topics (labels) ─────────────────────────────────
echo "→ Adding repository topics..."
gh repo edit "$GITHUB_USER/$REPO_NAME" \
  --add-topic quran \
  --add-topic islam \
  --add-topic prayer-times \
  --add-topic ramadan \
  --add-topic cli \
  --add-topic python \
  --add-topic terminal \
  --add-topic islamic

# ── 5. Push the code ───────────────────────────────────────
echo "→ Pushing code to GitHub..."
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
git branch -M main
git push -u origin main

# ── 6. Create initial release ──────────────────────────────
echo "→ Creating v1.0.0 release..."
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 \
  --title "quran-cli v1.0.0 — Initial Release" \
  --notes "## quran-cli v1.0.0

First public release of the Islamic terminal companion.

### Features
- Read all 114 Surahs by name or number with Arabic + 13 languages
- Accurate prayer times (8 calculation methods, auto-location)
- Ramadan sehri/iftar/tarawih schedule + 30-day calendar
- Eid ul-Fitr & Eid ul-Adha complete salah guides
- AI Quran & Hadith guide (RAG over authentic Kutub al-Sittah)
- 6 notification channels: Desktop, ntfy.sh, Telegram, WhatsApp, Gmail, Webhook
- Reading bookmarks, streak tracking, tafsir

\`\`\`bash
pip install quran-cli
quran schedule
\`\`\`

Built by [Md Zarif Azfar](https://mdzarifazfar.me)"

echo ""
echo "✓ Repository created: https://github.com/$GITHUB_USER/$REPO_NAME"
echo "✓ Release v1.0.0 published"
echo ""
echo "Next steps:"
echo "  1. Go to https://github.com/$GITHUB_USER/$REPO_NAME"
echo "  2. Add a repository social preview image (Settings → Social preview)"
echo "  3. Pin the repo to your profile"
