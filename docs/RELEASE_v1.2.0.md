## CHANGELOG — v1.2.0

### Bug Fixes

**Notifications (Critical)**
- `notify_all()` in `notifier.py` previously only fired desktop (plyer) + ntfy.sh.
  Telegram, WhatsApp, Gmail, and Webhook connectors were scheduled but never called.
  Fixed by introducing `dispatch_all()` which calls ALL configured channels.
- `scheduler.py` now uses `dispatch_all()` instead of `notify_all()`.
- APScheduler lambda pickling issue fixed — all job functions are now module-level
  (not lambdas/closures), preventing silent job failures on some platforms.
- Daemon reschedule at 00:05 now uses a temp-JSON config handoff instead of
  a captured closure, which was lost after process fork on macOS/Linux.
- Added `misfire_grace_time=300` (5 minutes) on all jobs — if the system
  was asleep at prayer time, the notification still fires within 5 minutes of waking.

**Quran Reading / Language**
- `read.py` no longer silently returns blank output when a surah is not cached.
  Now shows a clear error with actionable steps (check internet, try English first).
- New `--dual2` flag: shows primary translation + secondary translation (lang2)
  side by side — previously `--dual` only showed Arabic + primary.
- Language validation now prints a helpful message listing all valid codes.

### Changes
- Version: 1.1.8 → 1.2.0
- All 5 daily prayers + Sehri/Iftar/Tarawih + Laylatul Qadr alerts now reach
  Telegram, Gmail, WhatsApp, and Webhook in addition to desktop and ntfy.sh.

---

## Git commands to push v1.2.0

### Step 1 — copy the fixed files into your repo

```bash
# From the root of your quran-cli repo:

# Core fixes
cp notifier.py   quran/core/notifier.py
cp scheduler.py  quran/core/scheduler.py
cp read.py       quran/commands/read.py

# Version bump
cp __init__.py   quran/__init__.py
cp pyproject.toml pyproject.toml
```

### Step 2 — stage and commit

```bash
git add quran/core/notifier.py \
        quran/core/scheduler.py \
        quran/commands/read.py \
        quran/__init__.py \
        pyproject.toml

git commit -m "fix: notifications, language display, scheduler (v1.2.0)

- dispatch_all(): fire Telegram/Gmail/WhatsApp/Webhook from prayer scheduler
- scheduler: use module-level job fns (not lambdas) for APScheduler safety
- scheduler: misfire_grace_time=300 so sleep-woken devices still notify
- read.py: clear error on empty fetch instead of silent blank screen
- read.py: --dual2 flag for primary + secondary lang side by side
- bump version 1.1.8 → 1.2.0"
```

### Step 3 — tag and push

```bash
git tag v1.2.0
git push origin main
git push origin v1.2.0
```

### Step 4 — create GitHub release

```bash
gh release create v1.2.0 \
  --title "quran-cli v1.2.0 — Notification & Language Fixes" \
  --notes "## What changed

### Critical fixes
- **Telegram / Gmail / WhatsApp notifications** — were silently skipped in the scheduler.
  All 5 daily prayers + Sehri/Iftar/Laylatul Qadr now reach every configured channel.
- **Quran language display** — silent blank screen on first-run API miss replaced with
  a clear error and actionable steps.
- **Scheduler safety** — APScheduler lambda pickling issue fixed; prayer jobs no
  longer silently fail on macOS after fork.

### New
- \`quran read <surah> --dual2\` — shows primary + secondary language side by side.

### Install / Upgrade
\`\`\`bash
# macOS
pip3 install --upgrade quran-cli

# Linux / Windows
pip install --upgrade quran-cli
\`\`\`"
```

### Step 5 (optional) — update PyPI

```bash
# Build
python3 -m build          # macOS
python  -m build          # Linux/Windows

# Upload
python3 -m twine upload dist/quran_cli-1.2.0*   # macOS
python  -m twine upload dist/quran_cli-1.2.0*   # Linux/Windows
```
