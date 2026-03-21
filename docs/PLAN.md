# quran-cli — Full Technical Plan
> Version 2.0 · Comprehensive Islamic Terminal Companion

---

## Vision

A production-grade, terminal-native Islamic companion that feels as intentional as `git` or `gh`. Every feature is purposeful. No filler. The aesthetic: deep phosphor dark terminal, IBM Plex Mono, Islamic emerald accent (#10b981), amber for Ramadan (#f59e0b). It should feel like a tool a developer who takes their deen seriously would open every single day.

---

## Architecture Overview

```
quran-cli/
├── quran/
│   ├── cli.py                    # Typer root + callback
│   ├── commands/                 # One command per file
│   │   ├── read.py               # quran read
│   │   ├── search.py             # quran search
│   │   ├── pray.py               # quran pray
│   │   ├── schedule.py           # quran schedule (default view)
│   │   ├── ramadan.py            # quran ramadan
│   │   ├── eid.py                # quran eid
│   │   ├── remind.py             # quran remind
│   │   ├── news.py               # quran news
│   │   ├── bookmark.py           # quran bookmark
│   │   ├── tafsir.py             # quran tafsir
│   │   ├── config.py             # quran config
│   │   ├── quote.py              # quran quote
│   │   ├── streak.py             # quran streak
│   │   ├── guide.py              # quran guide (AI RAG)
│   │   └── connect.py            # quran connect
│   ├── core/                     # Business logic, zero UI
│   │   ├── prayer_times.py       # Pure-Python Adhan algorithm
│   │   ├── quran_engine.py       # Fetch + SQLite cache
│   │   ├── location.py           # IP geolocation + manual
│   │   ├── ramadan.py            # Hijri calendar, Ramadan utils
│   │   ├── scheduler.py          # APScheduler daemon
│   │   ├── notifier.py           # plyer + ntfy.sh dispatcher
│   │   ├── streak.py             # Reading/fasting tracker
│   │   ├── bookmark_store.py     # Named reading positions
│   │   └── ai/
│   │       ├── rag_engine.py     # Quran+Hadith RAG system
│   │       ├── hadith_store.py   # Authentic hadith database
│   │       └── embeddings.py     # Semantic search layer
│   ├── connectors/               # Notification channels
│   │   ├── base.py               # Abstract connector interface
│   │   ├── telegram_bot.py       # Telegram notifications
│   │   ├── whatsapp.py           # WhatsApp via Twilio
│   │   ├── gmail_connector.py    # Gmail reminders
│   │   ├── desktop.py            # OS notifications (plyer)
│   │   └── ntfy_connector.py     # ntfy.sh push
│   ├── ui/
│   │   └── renderer.py           # Rich console helpers
│   └── config/
│       └── settings.py           # TOML config loader/writer
├── tests/
│   ├── test_core.py
│   ├── test_prayer_times.py
│   ├── test_ramadan.py
│   ├── test_connectors.py
│   └── test_rag.py
├── docs/
│   ├── PLAN.md                   # This file
│   ├── COMMANDS.md               # Full command reference
│   └── CONNECTORS.md             # Connector setup guide
├── pyproject.toml
├── README.md
└── install.sh                    # One-line installer
```

---

## Phase 1 — Core Reading Engine ✅

**Goal:** Ship a usable Quran reader to PyPI.

### Technical Details

**Quran data source:**
- Primary: AlQuran.cloud REST API (`https://api.alquran.cloud/v1/`)
- Fallback: Bundled SQLite database (`quran.db`)
- 114 surahs × 6236 ayahs × N languages = cached on demand
- SQLite schema: `ayahs(surah, ayah, lang, text, transliteration)` — PRIMARY KEY (surah, ayah, lang)

**Arabic rendering:**
- `arabic-reshaper` — reshapes Arabic glyphs for correct ligature joining
- `python-bidi` — BiDi algorithm for right-to-left display in terminals
- Fallback: raw Unicode (still readable in most modern terminals)

**Languages supported:** en, bn, ar, ur, tr, fr, id (any edition on AlQuran.cloud API)

**Config:** TOML at `~/.config/quran-cli/config.toml`, written with a minimal hand-rolled TOML serializer (no extra deps)

### Deliverables
- [x] `quran read 1`, `quran read 2:255`, `quran read 18:1-10`
- [x] `--lang`, `--dual`, `--arabic/--no-arabic` flags
- [x] Auto-mark reading streak on read
- [x] SQLite cache (offline-first after first fetch)
- [x] `quran search "patience"` — full-text search in cached surahs
- [x] `quran tafsir 2:255` — Ibn Kathir brief via AlQuran.cloud

---

## Phase 2 — Prayer Times + Local Reminders ✅

**Goal:** Accurate prayer times anywhere on Earth, background reminders.

### Technical Details

**Prayer calculation — pure Python Adhan implementation:**

The algorithm derives prayer times from solar geometry:
1. Compute Julian Day Number for the date
2. Calculate sun's declination and equation of time
3. Derive solar noon (Dhuhr)
4. Compute hour angles for each prayer using target altitude:
   - Fajr / Isha: configured angle (e.g. 18° for Karachi)
   - Sunrise / Maghrib: −0.8333° (standard horizon correction)
   - Asr: `atan(1 / (shadow_factor + tan(|lat − dec|)))` — shadow factor = 1 (Standard) or 2 (Hanafi)
5. Convert fractional hours → `datetime`

**Methods supported:** Karachi (HMB), ISNA, MWL, Makkah (Umm Al-Qura), Egypt, Tehran, Turkey, Singapore

**Location detection:**
- Auto: `ip-api.com/json` — free, no key, returns city/country/lat/lon/timezone
- Manual: stored in config TOML, used when `auto = false`
- Cached in `_CACHE` module variable per process

**Scheduler daemon:**
- `APScheduler 3.x` BlockingScheduler with `date` triggers
- Unix: double-fork daemonization, PID stored in `~/.local/share/quran-cli/daemon.pid`
- Windows: inline blocking (no fork)
- Auto-reschedules at 00:05 AM each day for fresh prayer times
- Ramadan mode: adds Sehri warning (15 min before Fajr) + Iftar warning + Iftar trigger
- Reading goal: `date` trigger at configured time

**Sehri/Iftar timing:**
- Sehri = Fajr (Subh Sadiq) − 5 minutes
- Iftar = Maghrib (exact sunset)

### Deliverables
- [x] `quran pray` — table of 5 times
- [x] `quran pray next` — Rich panel countdown
- [x] `quran pray setup` — interactive wizard (IP detect or manual + method)
- [x] `quran remind on/off/status`
- [x] `quran remind set --goal 5ayah --at 20:00`
- [x] `quran remind phone` — ntfy.sh QR link
- [x] Background daemon with Ramadan-aware alerts

---

## Phase 3 — Cross-Device Notifications ✅

**Goal:** Prayer times and Ramadan alerts on every device, every channel.

### Connector Architecture

Each connector implements the `BaseConnector` abstract interface:

```python
class BaseConnector:
    name: str
    def send(self, title: str, body: str, **kwargs) -> bool: ...
    def test(self) -> bool: ...
    def setup(self) -> None: ...  # interactive wizard
```

**Dispatcher** (`notifier.py`): iterates enabled connectors, sends in parallel threads.

### Connectors

#### 1. Desktop (plyer) — built-in
- OS-native notifications on Linux, macOS, Windows
- No setup required
- Falls back to `print()` if plyer unavailable

#### 2. ntfy.sh — built-in
- Free, open-source, no account
- User subscribes to `quran-<random-hex>` topic on their phone
- QR code displayed in terminal via `qrcode` ASCII
- Works on any device with ntfy app (iOS/Android) or ntfy CLI

#### 3. Telegram Bot
- User creates a bot via @BotFather (free, 30 seconds)
- Wizard: paste bot token + chat ID (auto-detected on first message)
- Library: `python-telegram-bot` (async, well-maintained)
- Supports rich formatting: bold prayer names, emoji, inline links
- Message template:
  ```
  🕌 *Fajr* — 04:47 AM
  📍 Dhaka, Bangladesh
  ⏱ in 1h 23m
  ```

#### 4. WhatsApp (Twilio)
- Requires Twilio account (free sandbox for testing, ~$0.005/msg paid)
- User provides: Account SID, Auth Token, WhatsApp number
- Messages sent via Twilio WhatsApp API
- Alternative: Meta Cloud API (free 1000 msgs/month) — requires Meta business account
- Template messages only (WhatsApp policy) for business-initiated messages
- Sandbox allows free testing without approval

#### 5. Gmail
- Uses `smtplib` + App Password (no OAuth needed)
- User provides: Gmail address + App Password
- Generates clean HTML email for prayer schedule
- Daily digest mode: one email at Fajr with full day schedule
- Per-prayer mode: individual emails at each prayer time

#### 6. Custom Webhook
- POST JSON payload to any URL
- Enables: Discord, Slack, custom apps, Home Assistant, IFTTT
- Payload: `{ "type": "prayer", "name": "Fajr", "time": "04:47", "location": "Dhaka" }`

### Connector Storage
Connector credentials stored encrypted in `~/.config/quran-cli/connectors.json`:
```json
{
  "telegram": { "enabled": true, "token": "...", "chat_id": "..." },
  "whatsapp": { "enabled": false, "sid": "...", "token": "...", "to": "+880..." },
  "gmail":    { "enabled": false, "from": "...", "app_password": "...", "to": "..." },
  "webhook":  { "enabled": false, "url": "https://..." }
}
```

Basic XOR obfuscation (not encryption) — credentials are sensitive, document clearly.

### Deliverables
- [x] `quran connect list` — show all connectors + status
- [x] `quran connect telegram` — setup wizard
- [x] `quran connect whatsapp` — setup wizard
- [x] `quran connect gmail` — setup wizard
- [x] `quran connect webhook` — setup URL
- [x] `quran connect test <channel>` — send test notification
- [x] `quran connect off <channel>` — disable connector

---

## Phase 4 — Ramadan + Eid + Schedule ✅

**Goal:** Complete Ramadan and Eid experience in the terminal.

### Ramadan Features

**Hijri calendar** — approximation using:
```python
JD = 367*y - 7*(y+(m+9)//12)//4 + 275*m//9 + d + 1721013.5
# convert JD to Hijri via Kuwaiti algorithm
```
Known Ramadan start dates hardcoded for 1444–1449 AH (2023–2027) for accuracy.

**Monthly timetable:**
- Computes 30 days of prayer times in one call
- Sehri = Fajr − 5 min, Iftar = Maghrib
- Tarawih = Isha + 1h 30m (configurable)
- Fast duration per day

**Laylatul Qadr:** Highlight on nights 21, 23, 25, 27, 29 of Ramadan

**Fasting streak tracker** — JSON at `~/.local/share/quran-cli/streak.json`

### Eid Features

**Eid ul-Fitr (1447 AH = ~20 March 2026):**
- Sunnah acts checklist
- Step-by-step salah guide (9 steps, including Khutbah after prayer)
- Zakat ul-Fitr details
- Takbeer text: Arabic + transliteration + meaning

**Eid ul-Adha (1447 AH = ~27 May 2026):**
- Salah same as Fitr (2 rak'ah, extra Takbeers)
- Qurbani animal guide (Goat: 1 person, Cow/Camel: up to 7)
- Slaughter window: 10th–12th Dhul Hijjah
- Meat distribution: 1/3 self · 1/3 relatives · 1/3 poor
- Takbeer al-Tashreeq: from Fajr 9th to Asr 13th

### Schedule View
- Full-day timeline with Rich progress bars
- Status: done (past) · next (upcoming, highlighted green) · open
- Ramadan mode: adds Sehri, Iftar, Tarawih rows in amber
- Fast duration bar with percentage
- Toggle: `--ramadan / --normal` flag

---

## Phase 5 — Quran Guide AI (RAG System) ✅

**Goal:** Ask questions, get answers grounded in Quran and authentic Hadith.

### Architecture

```
User query
    ↓
Query preprocessing (clean, normalize)
    ↓
Semantic search → Quran corpus (6236 ayahs)
                → Hadith corpus (Sahih Bukhari, Sahih Muslim selections)
    ↓
Top-K retrieval (k=5 ayahs + k=3 hadith)
    ↓
Context assembly
    ↓
LLM completion (Anthropic claude-sonnet-4-20250514)
    ↓
Response with citations (surah:ayah, hadith reference)
```

### RAG Technical Stack

**Embeddings:**
- Option A: `sentence-transformers` (`all-MiniLM-L6-v2`, 80MB) — fully offline
- Option B: TF-IDF + BM25 (`rank-bm25` library) — faster, no model download, less semantic
- Default: TF-IDF/BM25 (works offline, zero ML deps)
- Optional: semantic mode enabled with `quran config set ai.embeddings sentence-transformers`

**Vector store:** SQLite with JSON blob (no Chroma/FAISS dep, keeps install simple)
```sql
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,      -- e.g. "quran:2:255" or "hadith:bukhari:1:1"
    source TEXT,              -- "quran" | "hadith"
    reference TEXT,           -- "Al-Baqarah 2:255"
    text TEXT,                -- English/Arabic text
    keywords TEXT,            -- JSON array for BM25
    embedding BLOB            -- float32 array if using sentence-transformers
);
```

**Hadith corpus:**
- Sahih Bukhari (top 500 most-referenced hadith)
- Sahih Muslim (top 300)
- Abu Dawud (top 100 — fiqh-focused)
- Source: `hadith-api.vercel.app` (free) or bundled JSON
- Each hadith tagged: topic tags (prayer, fasting, charity, etc.)

**LLM prompting:**
```
System: You are a knowledgeable Islamic scholar assistant. Answer ONLY based on 
the provided Quran verses and authentic Hadith. If the answer is not in the 
provided context, say so clearly. Do not fabricate hadith. Cite every claim.

Context:
[QURAN] Al-Baqarah 2:186 — "And when My servants ask you concerning Me..."
[HADITH] Sahih Bukhari 8:395 — "The Prophet (ﷺ) said..."

User question: {query}

Answer with citations. Mark authenticity: (Sahih/Hasan/Da'if).
```

**Thinking mode:** Uses Anthropic extended thinking for complex fiqh questions.

**Authenticity filter:**
- Only Sahih (authentic) and Hasan (good) hadith in the corpus
- Da'if (weak) hadith clearly marked if included
- No unverified social media quotes
- Source attribution on every response

### Deliverables
- [x] `quran guide "how to perform wudu"` — instant answer with citations
- [x] `quran guide "what does the Quran say about patience"` — ayah search
- [x] `quran guide --hadith "sunnah of eating"` — hadith-focused search
- [x] `quran guide --interactive` — multi-turn chat mode
- [x] Offline mode (BM25 search, no LLM) for no-API use
- [x] Citation format: `[Quran 2:186]` `[Bukhari 8:395]`

---

## Phase 6 — Full Schedule UI ✅

**Goal:** The flagship `quran schedule` command — a complete day view.

### Schedule Command Features
- **Live countdown** to next prayer, refreshed every second (`--live` flag)
- **Progress bars** per prayer (filled = time elapsed since previous prayer)
- **Ramadan mode** auto-detected: amber rows for Sehri, Iftar, Tarawih
- **Fast duration** bar: shows % of today's fast completed
- **7-day view** (`--week`): compact table of all prayers for the week
- **Monthly view** (`--month`): Ramadan-specific full calendar
- **Date override** (`--date 2026-03-25`)

### Namaz Guide
Interactive prayer picker in terminal:
- Select Fajr/Dhuhr/Asr/Maghrib/Isha
- Shows: Arabic name, time today, rakah breakdown (color-coded dots)
- Description of the prayer's significance
- Sunnah acts before/after

---

## Technical Stack Summary

| Layer | Technology | Reason |
|---|---|---|
| CLI framework | Typer | Typer > Click for modern Python; auto-generates --help |
| Terminal UI | Rich | Best-in-class terminal rendering |
| HTTP client | httpx | Async-ready, better than requests |
| Prayer algorithm | Pure Python | Zero deps, accurate, portable |
| Database | SQLite (stdlib) | No dep, offline-first |
| Scheduler | APScheduler | Battle-tested, supports cron/interval/date |
| Desktop notify | plyer | Cross-platform (Linux/macOS/Windows) |
| Phone push | ntfy.sh | Free, open-source, no account |
| Telegram | python-telegram-bot | Official library, async |
| WhatsApp | Twilio SDK | Most reliable API |
| Email | smtplib (stdlib) | No dep for Gmail SMTP |
| AI/RAG | anthropic SDK | Claude claude-sonnet-4-20250514 with extended thinking |
| Embeddings | rank-bm25 (BM25) | Offline, fast, no ML required |
| Arabic text | arabic-reshaper + python-bidi | Correct RTL terminal rendering |
| Config | TOML (stdlib 3.11+) | Human-readable, no deps |
| Packaging | hatchling | Modern, simple |
| Distribution | PyPI + Homebrew tap | pip install + brew install |

---

## Distribution

### PyPI
```bash
pip install quran-cli
```
Entry point: `quran = quran.cli:app`

### Homebrew Tap
```ruby
# Formula/quran-cli.rb
class QuranCli < Formula
  desc "Islamic terminal companion — Quran, prayer times, Ramadan, Eid"
  homepage "https://github.com/zaryif/quran-cli"
  url "https://files.pythonhosted.org/..."
  depends_on "python@3.11"
  def install
    virtualenv_install_with_resources
  end
end
```

### One-line install
```bash
curl -fsSL https://raw.githubusercontent.com/zaryif/quran-cli/main/install.sh | bash
```

### Docker
```dockerfile
FROM python:3.11-slim
RUN pip install quran-cli
ENTRYPOINT ["quran"]
```

---

## Data Files

| File | Location | Size | Description |
|---|---|---|---|
| `quran.db` | `~/.local/share/quran-cli/` | ~15MB (all langs) | Cached Quran text |
| `hadith.db` | `~/.local/share/quran-cli/` | ~8MB | Authentic hadith corpus |
| `streak.json` | `~/.local/share/quran-cli/` | <1KB | Reading/fasting streaks |
| `bookmarks.json` | `~/.local/share/quran-cli/` | <1KB | Named positions |
| `daemon.pid` | `~/.local/share/quran-cli/` | <1KB | Scheduler PID |
| `config.toml` | `~/.config/quran-cli/` | ~2KB | User settings |
| `connectors.json` | `~/.config/quran-cli/` | ~1KB | Connector credentials |

---

## Roadmap (Future)

### v1.1
- [ ] `quran read --interactive` — arrow-key pager (Textual TUI)
- [ ] Hijri date in schedule header
- [ ] Tasbih counter (`quran tasbih`)
- [ ] Export Ramadan calendar to PDF/CSV/iCal

### v1.2
- [ ] macOS menu bar widget (rumps library)
- [ ] Android Termux one-liner install
- [ ] Arabic-only terminal mode (no translation)
- [ ] Quran audio reciter download (Mishary Rashid, etc.)

### v2.0
- [ ] Local LLM support (Ollama integration for offline AI guide)
- [ ] Qibla direction in terminal (ASCII compass from GPS)
- [ ] Zakat calculator (`quran zakat`)
- [ ] Islamic finance tracker (`quran halal finance`)
- [ ] Community features: share Ramadan schedule

---

## Security & Privacy

- **Location**: IP-API geolocation, no persistent server logging
- **No telemetry**: zero analytics, no phone-home
- **Credentials**: stored in `~/.config/quran-cli/connectors.json` — file permission 600
- **ntfy.sh**: random hex topic ID, not linked to identity
- **AI queries**: sent to Anthropic API (subject to their privacy policy) — opt-in only
- **Hadith corpus**: bundled locally, no query sent for hadith search

---

## Development Setup

```bash
git clone https://github.com/zaryif/quran-cli
cd quran-cli
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest tests/ -v
```

### Running tests
```bash
pytest tests/test_prayer_times.py -v    # prayer time accuracy
pytest tests/test_ramadan.py -v         # Hijri calendar
pytest tests/test_connectors.py -v      # connector mocking
pytest tests/test_rag.py -v             # AI guide (requires ANTHROPIC_API_KEY)
```

### Environment variables
```bash
ANTHROPIC_API_KEY=sk-ant-...    # for quran guide AI feature
QURAN_CLI_CONFIG=~/.config/...  # override config path
QURAN_CLI_DEBUG=1               # verbose logging
```
