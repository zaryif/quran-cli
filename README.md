<div align="center">

<br/>

# بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ

*In the name of Allah, the Most Gracious, the Most Merciful*

<br/>

# quran-cli

**The Islamic terminal companion — for developers who take their deen seriously.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)

</div>

---

```
بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ
In the name of Allah, the Most Gracious, the Most Merciful

  Created by Md Zarif Azfar

  quran schedule                     full day view — prayers, sehri, iftar
  quran read 1                       read Al-Fatihah
  quran read kahf                    read by name
  quran read 2:255                   single ayah
  quran read 2:1-10                  ayah range
  quran search "patience"            search across the Quran
  quran pray                         prayer times for your location
  quran clock                        live prayer clock with seconds
  quran ramadan                      sehri, iftar & tarawih times
  quran namaz                        prayer details & rakat breakdown
  quran fasting                      daily sahur & iftar times
  quran lock                         screen lock with PIN protection
  quran lang                         change display language
  quran connect                      notification channels
  quran hadith                      interactive edition & book browser
  quran hadith daily                today's hadith of the day
  quran hadith browse <edition>      browse books within an edition
  quran hadith read <edition> <num>  read specific hadith
  quran hadith search "patience"     search hadith by topic
  quran guide "how to make wudu"     AI-powered guide via Gemini
  quran quote                        random ayah quote
  quran streak                       your reading activity
  quran bookmark                     save positions
  quran tafsir                       tafsir for any ayah
  quran info surahs                  list all 114 surahs
  quran cache download               pre-download data for offline reading
  quran config set key val           change a setting
  quran update                       update quran-cli to latest version
  quran --help                       full help
```

---

## What is quran-cli?

A full-featured Islamic companion that lives in your terminal. Prayer times calculated precisely for your location. Every Surah in 13 languages. Ramadan sehri and iftar times. Eid salah guides. A Quran + Hadith AI guide. Reminders pushed to your phone, Telegram, Gmail, or WhatsApp — all from a single `quran` command.

Built with care by [Md Zarif Azfar](https://mdzarifazfar.me) — a Muslim developer from Dhaka, Bangladesh.

---

## Features

| | Feature | Command |
|---|---|---|
| 📖 | Read any Surah by number or name | `quran read kahf` |
| 🔤 | Arabic text + 13 language translations | `quran read 36 --dual` |
| 🔍 | Full-text Quran search (live API) | `quran search "patience"` |
| 🕌 | Accurate prayer times (8 methods) | `quran pray` |
| 🕐 | Live prayer clock with countdown | `quran clock` |
| 📅 | Full-day Islamic schedule | `quran schedule` |
| ☽  | Ramadan sehri, iftar, tarawih | `quran ramadan` |
| 🌙 | Daily fasting times + Sunnah days | `quran fasting` |
| ✦  | Eid ul-Fitr & Eid ul-Adha guide | `quran eid fitr` |
| 🙏 | How-to for every Salah | `quran namaz fajr` |
| 🤲 | Quran & Hadith AI guide (RAG) | `quran guide "..."` |
| 🔒 | Terminal screen lock with PIN | `quran lock` |
| 📱 | Phone push via ntfy.sh (free, QR) | `quran connect ntfy` |
| 💬 | Telegram prayer reminders | `quran connect telegram` |
| 📧 | Gmail daily digest | `quran connect gmail` |
| 📲 | WhatsApp alerts (Twilio) | `quran connect whatsapp` |
| 🔗 | Discord/Slack webhook | `quran connect webhook` |
| 📰 | Muslim world news (RSS) | `quran news` |
| 🔖 | Reading bookmarks | `quran bookmark save "fajr" 18:1` |
| 📊 | Reading & fasting streaks | `quran streak` |
| 📖 | Tafsir (Ibn Kathir) | `quran tafsir 2:255` |

---

### **⭐ One-Liner Install (from GitHub)**

```bash
pip3 install git+https://github.com/zaryif/quran-cli.git
```

### **⭐ Recommended Installation (v1.3.0)**
Clone and install from source for development:

```bash
git clone https://github.com/zaryif/quran-cli.git
cd quran-cli
pip install -e .          # pip3 install -e . on macOS
quran
```

### Optional extras

```bash
pip install -e ".[ai]"          # AI guide (requires ANTHROPIC_API_KEY)
pip install -e ".[connectors]"  # Telegram + WhatsApp
pip install -e ".[all]"         # Everything
# macOS: replace pip → pip3 in all commands above
```

### **Running Locally (Alternative / Manual)**
If `pip install -e .` fails due to network or build issues, you can run the CLI directly from the source.

#### **macOS & Linux**
```bash
export PYTHONPATH=.
python3 -m quran gui    # or any other command
```

#### **Windows (PowerShell)**
```powershell
$env:PYTHONPATH="."
$env:PYTHONIOENCODING="utf-8"
python -m quran gui
```

#### **Windows (Command Prompt)**
```cmd
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8
python -m quran gui
```

---

## Quick Start

```bash
quran                        # welcome screen with Basmallah
quran schedule               # full day — auto-detects Ramadan, shows sehri/iftar
quran pray                   # today's 5 prayer times (auto-detected location)
quran pray next              # countdown to next prayer
quran pray setup             # set location + calculation method
quran clock                  # live prayer clock with seconds + countdown
quran fasting                # today's sahur & iftar times + Sunnah days
quran lock                   # lock the screen (PIN or Ctrl+C)
quran cache download         # cache all 114 surahs for fully offline reading
```

---

## Reading the Quran

```bash
# By number
quran read 1                 # Al-Fatihah
quran read 2                 # Al-Baqarah (full)

# By name — flexible matching
quran read kahf              # Al-Kahf
quran read "ya-sin"          # Ya-Sin
quran read rahman            # Ar-Rahman
quran read ikhlas            # Al-Ikhlas

# Specific ayahs
quran read 2:255             # Ayat ul-Kursi
quran read 2:1-10            # Range

# Language options
quran read 36 --lang bn      # Bangla
quran read 36 --lang ur      # Urdu
quran read 36 --lang ar      # Arabic only
quran read 36 --dual         # Arabic + translation side by side

# Text size — small, medium (default), large
quran read 1 --size small    # compact: ref + text, no Arabic
quran read 1 --size large    # panel-wrapped with borders + padding
quran read 1 --dual --size large  # Arabic + translation in panels

# Reading mode — full (default), ayah, page
quran read 18 --mode page    # 5 ayahs per page (Enter/n/p/q)
quran read 18 --mode ayah    # one ayah at a time (Enter/n/p/s/q)
quran read 36 --mode page --size large  # both combined

# Interactive navigator
quran read                   # opens Surah + Language + Size picker

# Search
quran search "patience"
quran search "sabr" --lang ar

# Tafsir
quran tafsir 2:255
```

**Supported languages:**

| Code | Language | Translator |
|---|---|---|
| `en` | English | Sahih International |
| `bn` | Bengali/Bangla | — |
| `ar` | Arabic | Original (Mushaf) |
| `ur` | Urdu | Jalandhry |
| `tr` | Turkish | Diyanet |
| `fr` | French | Hamidullah |
| `id` | Indonesian | Kementerian Agama |
| `ru` | Russian | Kuliev |
| `de` | German | Bubenheim |
| `es` | Spanish | Cortes |
| `zh` | Chinese | Jian |
| `nl` | Dutch | Keyzer |
| `ms` | Malay | Basmeih |

---

## Prayer Times

```bash
quran pray                   # today's prayer times
quran pray next              # countdown to next prayer
quran pray setup             # interactive setup wizard

# Schedule views
quran schedule               # today's full Islamic schedule
quran schedule --week        # 7-day timetable
quran schedule --date 2026-04-01
```

**Supported calculation methods:**

| Method | Region |
|---|---|
| `Karachi` | South Asia, UK (HMB) |
| `ISNA` | North America |
| `MWL` | Muslim World League |
| `Makkah` | Saudi Arabia, Gulf |
| `Egypt` | Egypt, Sudan |
| `Turkey` | Turkey (Diyanet) |
| `Singapore` | Singapore, Malaysia |
| `Tehran` | Iran |

```bash
quran pray setup             # interactive method selection
quran config set method Karachi
quran config set asr_method Hanafi   # Standard or Hanafi
```

---

## Prayer Clock

Live full-screen prayer clock with seconds-level countdown and all 5 Waqt times.

```bash
quran clock                  # live clock — Ctrl+C to exit
```

Shows: current time with seconds · Hijri date · 5-waqt Namaz times · next prayer countdown · Sehri/Iftar during Ramadan. Updates every second. Works on macOS, Linux, and Windows Terminal.

---

## Ramadan

```bash
quran ramadan                # today: sehri time, fast progress, iftar countdown
quran ramadan --week         # 7-day sehri/iftar table
quran ramadan --month        # full 30-day Ramadan calendar
quran ramadan --fast         # mark today's fast as complete (+streak)
```

Output includes:
- Sehri end time (Imsak — 5 min before Fajr)
- Iftar time (exact Maghrib/sunset)
- Tarawih time (Isha + 1.5h)
- Fast duration (hours and minutes)
- Laylatul Qadr nights highlighted (21, 23, 25, 27, 29)

---

## Fasting Times

Daily fasting times for any day of the year — not just Ramadan.

```bash
quran fasting                # today's sahur & iftar times
quran fasting --week         # 7-day fasting schedule
quran fasting --date 2026-04-01  # specific date
```

Highlights Sunnah fasting days: Monday, Thursday, White Days (13–15 Hijri), Day of Arafah, Ashura, and Shawwal.

---

## Eid Guide

```bash
quran eid                    # next Eid dates overview
quran eid fitr               # Eid ul-Fitr — 9-step salah guide + Zakat ul-Fitr
quran eid adha               # Eid ul-Adha — Qurbani guide + meat distribution
quran eid --takbeer          # Takbeer text: Arabic + transliteration + meaning
```

---

## Salah Guide

```bash
quran namaz                  # interactive picker
quran namaz fajr
quran namaz dhuhr
quran namaz asr
quran namaz maghrib
quran namaz isha
quran namaz jummah           # Friday prayer
quran namaz tarawih          # Ramadan night prayer
quran namaz witr             # Witr guide with Qunoot
```

Each prayer shows: rakah breakdown (Sunnah/Fard/Nafl), Arabic name, significance, common mistakes.

---

## Screen Lock

Lock your terminal with an optional PIN. Shows prayer times, Hijri date, and live clock while locked.

```bash
quran lock                   # lock screen (Ctrl+C or PIN to unlock)
quran lock setup             # set or change your PIN
quran lock off               # remove PIN and disable lock
```

Works on macOS, Linux, and Windows. PIN is SHA-256 hashed and stored locally in `~/.config/quran-cli/config.toml`.

---

## AI Guide

Ask questions answered directly from the Quran and authentic Hadith:

```bash
quran guide "how to perform wudu"
quran guide "what does the Quran say about patience"
quran guide "ruling on fasting for travelers" --hadith
quran guide --interactive             # multi-turn conversation
quran guide --offline "tawakkul"     # BM25 search only, no API needed
```

## Hadith

Browse and search authentic Hadith from the Kutub al-Sittah (Bukhari, Muslim, etc.) and many other collections in multiple languages.

```bash
quran hadith                 # interactive edition & book browser
quran hadith daily           # today's hadith of the day
quran hadith browse <edition> # browse books within an edition
quran hadith read <edition> <num> # read specific hadith

# During reading:
# n: next hadith in section
# p: previous hadith in section
# q: back to section list
```

**How it works:**
1. Fetches live from fawazahmed0/hadith-api (jsDelivr CDN).
2. Supports 50+ editions including translations in 10+ languages.
3. Only Sahih and Hasan grade hadith included.

```bash
export ANTHROPIC_API_KEY=sk-ant-...    # for AI-generated answers
# Without key: shows source passages only (offline BM25 mode)
```

---

## Notifications & Reminders

### Start the daemon

```bash
quran remind on              # start background prayer reminder daemon
quran remind set --at 20:00         # set reading reminder time
quran remind set --prayers fajr,asr # trigger only specific prayers (or 'all' / 'none')
quran remind set --advance 15       # get text notifications 15 mins before prayer (free, no account)
```

### Link your phone (free, no account)

```bash
quran connect ntfy           # generates ntfy.sh topic + QR code
# Install ntfy app → subscribe → receive prayer alerts on your phone
```

### All channels

**Improvements:**
- **Telegram Bot Timezone**: The Telegram bot now accurately determines your timezone based on your location, ensuring precise prayer times.
- **Ntfy.sh Test**: The `quran remind test` command now correctly dispatches test notifications to your configured ntfy.sh channel.

```bash
quran connect list           # all channels + status
quran connect telegram       # Telegram bot (free, 30-second setup)
quran connect gmail          # Gmail daily digest
quran connect whatsapp       # WhatsApp via Twilio
quran connect webhook <url>  # Discord, Slack, Home Assistant, custom
quran connect test telegram  # verify a channel
```

**All channels receive:**
- Fajr, Dhuhr, Asr, Maghrib, Isha notifications
- Sehri warning (15 min before end) during Ramadan
- Iftar alert during Ramadan
- Daily Quran reading reminder
- Laylatul Qadr nights (last 10 days of Ramadan)

---

## Configuration

Config lives at `~/.config/quran-cli/config.toml`:

```toml
lang         = "en"
method       = "Karachi"     # prayer calculation method
asr_method   = "Standard"    # Standard or Hanafi

[location]
city    = "Dhaka"
country = "BD"
lat     = 23.8103
lon     = 90.4125
tz      = "Asia/Dhaka"
auto    = true               # re-detect on next run

[remind]
enabled    = false
goal_ayahs = 5
goal_time  = "20:00"

[ramadan]
notify_sehri_min = 15        # alert N min before sehri ends
notify_iftar_min = 15        # alert N min before iftar
```

```bash
quran config show
quran config set lang bn
quran config set method Karachi
quran config set location auto    # re-run IP geolocation
quran config reset                # reset to defaults
```

---

## Shell Integration

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Show daily ayah when opening a new terminal
quran quote 2>/dev/null

# Quick aliases
alias qs='quran schedule'
alias qp='quran pray next'
alias qr='quran read'
```

---

## Data Sources

All data is fetched from free, open, authenticated sources — no mock data anywhere:

| Source | Used for | API |
|---|---|---|
| **AlQuran.cloud** | All Quran text (90+ editions) | `api.alquran.cloud/v1/` |
| **fawazahmed0/hadith-api** | Authentic hadith corpus | `cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/` |
| **ip-api.com** | Auto location detection | `ip-api.com/json/` |
| **ntfy.sh** | Free phone push | `ntfy.sh/{topic}` |
| **IslamicAPI** | Daily fasting times | `islamicapi.com` |

All Quran text and hadith are cached locally after first fetch — works completely offline thereafter.

---

## Project Structure

```
quran-cli/
├── quran/
│   ├── __init__.py            # Version
│   ├── __main__.py            # python -m quran
│   ├── cli.py                 # Entry point + top-level commands
│   ├── commands/              # 26 command modules
│   │   ├── read.py            # quran read (by number, name, dual-language)
│   │   ├── pray.py            # prayer times + setup
│   │   ├── clock.py           # live prayer clock with seconds + countdown
│   │   ├── lock.py            # terminal screen lock with optional PIN
│   │   ├── schedule.py        # full day view
│   │   ├── ramadan.py         # Ramadan timings + calendar
│   │   ├── fasting.py         # daily sunnah fasting times
│   │   ├── eid.py             # Eid salah guide
│   │   ├── namaz.py           # salah performance guide
│   │   ├── hadith.py          # Hadith browser + daily + search
│   │   ├── guide.py           # AI Quran + Hadith RAG
│   │   ├── gui.py             # Interactive terminal dashboard
│   │   ├── connect.py         # notification channels
│   │   ├── remind.py          # notification wizard & daemon
│   │   ├── bot.py             # Cloud Telegram Bot
│   │   ├── bookmark.py        # universal Quran/Hadith bookmarks
│   │   ├── search.py          # full-text Quran search
│   │   ├── quote.py           # daily random ayah
│   │   ├── streak.py          # reading + fasting streaks
│   │   ├── tafsir.py          # Ibn Kathir tafsir
│   │   ├── news.py            # Muslim world RSS news
│   │   ├── lang.py            # language picker + config
│   │   ├── cache.py           # offline data download
│   │   ├── config.py          # config show/set/reset
│   │   └── update.py          # self-update from GitHub
│   ├── core/
│   │   ├── prayer_times.py    # Pure-Python Adhan algorithm
│   │   ├── quran_engine.py    # AlQuran.cloud + SQLite cache
│   │   ├── location.py        # IP geolocation
│   │   ├── ramadan.py         # Hijri calendar
│   │   ├── scheduler.py       # APScheduler daemon
│   │   ├── streak.py          # streak persistence
│   │   ├── bookmark_store.py  # bookmark persistence
│   │   ├── notifier.py        # notification dispatcher
│   │   └── ai/
│   │       └── rag_engine.py  # BM25 retrieval + LLM generation
│   ├── config/
│   │   └── settings.py        # TOML config load/save/defaults
│   ├── connectors/
│   │   └── connectors.py      # Desktop, ntfy, Telegram, WhatsApp, Gmail, Webhook
│   └── ui/
│       └── renderer.py        # Rich terminal renderer
├── tests/
│   ├── test_core.py           # Prayer times, Hijri, config tests
│   └── test_notifications_fix.py
├── README.md
├── INSTALL.md                 # Full installation guide
├── REQUIREMENTS.md
├── THINGS.md                  # Technical details + data authenticity
├── ABOUT.md                   # About the developer
├── Dockerfile                 # Docker for cloud Telegram bot
├── install.sh                 # One-liner installer script
├── pyproject.toml             # Package metadata + dependencies
└── docs/
    ├── PLAN.md                # Full architecture
    └── COMMANDS.md            # Complete command reference
```

---

## Development

```bash
git clone https://github.com/zaryif/quran-cli.git
cd quran-cli
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"    # inside venv, pip works on all platforms
pytest tests/ -v
```

```bash
# Run all tests
pytest tests/test_core.py -v

# With AI guide tests
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/test_rag.py -v
```

---

## Privacy

- **No telemetry.** Zero analytics, zero phone-home.
- **Quran text** cached locally in `~/.local/share/quran-cli/quran.db`
- **Location** detected via ip-api.com — stored in config, never sent elsewhere
- **Connector credentials** stored in `~/.config/quran-cli/connectors.json` (chmod 600)
- **AI queries** sent to the LLM API — opt-in, requires your own API key

---

## About

Built by **[Md Zarif Azfar](https://mdzarifazfar.me)** — a developer from Dhaka, Bangladesh.

Read more: [ABOUT.md](ABOUT.md)

---

## License

[MIT License](LICENSE) © 2026 Md Zarif Azfar

---

<div align="center">

*"Recite in the name of your Lord who created"* — Al-Alaq 96:1

</div>
