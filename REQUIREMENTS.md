# quran-cli Requirements

> Complete dependency manifest — every package, its purpose, and why it was chosen.

---

## Python Version

**Python 3.11+** required.

- Uses `tomllib` from stdlib (added in 3.11) — no `tomli` fallback needed
- Uses `zoneinfo` from stdlib (added in 3.9) — timezone-aware prayer times
- Uses `match` statements (added in 3.10)

## Terminal & Font Recommendations

To ensure the Arabic text, progress bars, and dashboard UI render perfectly, you must use a terminal that supports **True Color (24-bit)** and a good **monospaced developer font** (like *JetBrains Mono*, *Fira Code*, *Cascadia Code*, or *MesloLGS Nerd Font*).

### 🍎 macOS
* **[iTerm2](https://iterm2.com/) (Highly Recommended):** The gold standard for Mac developers. It handles the right-to-left Arabic rendering beautifully and supports rich colors natively.
* **[Ghostty](https://ghostty.org/) / [Alacritty](https://alacritty.org/):** GPU-accelerated terminals. Blazing fast, minimalistic, and renders the ASCII splash screen instantly.
* **Native Terminal:** Works flawlessly, though colors may appear slightly more muted than iTerm2.

### 🪟 Windows
* **[Windows Terminal](https://apps.microsoft.com/detail/9n0dx20hk701) (Highly Recommended):** The absolute best option for Windows. It natively supports Unicode, right-to-left languages (Arabic), and 24-bit color. Install it from the Microsoft Store.
* **[WezTerm](https://wezfurlong.org/wezterm/):** An incredibly powerful, cross-platform terminal emulator that perfectly parses complex CLI layouts.

### 🐧 Linux
* **[GNOME Terminal](https://help.gnome.org/users/gnome-terminal/stable/) / [Konsole](https://konsole.kde.org/):** Excellent default choices that handle True Color and Unicode natively.
* **[Kitty](https://sw.kovidgoyal.net/kitty/):** A highly customizable, GPU-accelerated terminal that renders the `rich` tables and borders phenomenally well.

---

## Core Dependencies

### CLI & Terminal UI

| Package | Version | Purpose |
|---|---|---|
| `typer` | `>=0.12.0` | CLI framework — auto-generates `--help`, sub-commands, type validation. Chosen over Click for cleaner Python-native syntax. |
| `rich` | `>=13.7.0` | Terminal rendering — panels, tables, progress bars, colours, markdown. Best-in-class terminal UI library for Python. |

### HTTP Client

| Package | Version | Purpose |
|---|---|---|
| `httpx` | `>=0.27.0` | HTTP requests to AlQuran.cloud, ip-api.com, ntfy.sh, Hadith API. Chosen over `requests` for async-readiness and better timeout handling. |

### Prayer Times Scheduling

| Package | Version | Purpose |
|---|---|---|
| `apscheduler` | `>=3.10.0` | Background daemon for prayer notifications. Manages `date`-triggered jobs, persists PID, handles midnight reschedule. |

### Notifications

| Package | Version | Purpose |
|---|---|---|
| `plyer` | `>=2.1.0` | Cross-platform desktop notifications (Linux/macOS/Windows). Provides `notification.notify()` that maps to OS-native popup. |
| `qrcode` | `>=7.4.2` | Generates ASCII QR codes for ntfy.sh phone link setup. Pure Python, no PIL required for ASCII output. |

### Arabic Text Rendering

| Package | Version | Purpose |
|---|---|---|
| `arabic-reshaper` | `>=3.0.0` | Reshapes Arabic characters into correct connected glyphs. Without this, Arabic renders as disconnected letters in most terminals. |
| `python-bidi` | `>=0.4.2` | BiDi (Bidirectional) algorithm — ensures Arabic reads right-to-left correctly in terminals that default to LTR. |

### News & Feeds

| Package | Version | Purpose |
|---|---|---|
| `feedparser` | `>=6.0.11` | Parses RSS/Atom feeds from Al Jazeera, SeekersGuidance, 5Pillars, IslamQA. Universal feed parser, handles malformed XML gracefully. |

### AI Guide (RAG)

| Package | Version | Purpose |
|---|---|---|
| `rank-bm25` | `>=0.2.2` | BM25 (Okapi BM25) ranking algorithm for semantic search over Quran+Hadith corpus. Fully offline — no model download required. |

---

## Optional Dependencies

### AI Answer Generation

| Package | Version | Purpose |
|---|---|---|
| `anthropic` | `>=0.28.0` | Anthropic API client for `quran guide` AI answers. Only needed if you want AI-generated answers with citations. Without it, `quran guide` shows BM25 search results only. |

**Setup:**
```bash
pip install quran-cli[ai]
export ANTHROPIC_API_KEY=sk-ant-...
quran guide "how to perform wudu"
```

### Telegram Notifications

| Package | Version | Purpose |
|---|---|---|
| `python-telegram-bot` | `>=21.0` | Telegram Bot API client. Only needed if using `quran connect telegram`. |

**Setup:**
```bash
pip install quran-cli[connectors]
quran connect telegram
```

### WhatsApp Notifications

| Package | Version | Purpose |
|---|---|---|
| `twilio` | `>=9.0` | Twilio REST API for WhatsApp messages. Only needed if using `quran connect whatsapp`. |

### Semantic Search (Better AI Guide)

| Package | Version | Purpose |
|---|---|---|
| `sentence-transformers` | `>=3.0` | Semantic embeddings for more accurate RAG retrieval. Downloads `all-MiniLM-L6-v2` (~80MB) on first use. Falls back to BM25 if not installed. |

**Setup:**
```bash
pip install quran-cli[all]  # includes everything
quran config set ai.embeddings sentence-transformers
```

---

## Development Dependencies

| Package | Version | Purpose |
|---|---|---|
| `pytest` | `>=8.0` | Test runner |
| `pytest-asyncio` | latest | Async test support |

```bash
pip install quran-cli[dev]
pytest tests/ -v
```

---

## Standard Library Modules Used

These are part of Python 3.11+ stdlib — no installation needed:

| Module | Usage |
|---|---|
| `sqlite3` | Local database for Quran text cache, RAG corpus, bookmarks, streaks |
| `tomllib` | TOML config file parsing (Python 3.11+) |
| `zoneinfo` | Timezone-aware prayer times (`Asia/Dhaka`, `Europe/London`, etc.) |
| `pathlib` | Cross-platform file paths |
| `smtplib` | Gmail SMTP for email notifications |
| `email.mime` | Email construction for Gmail connector |
| `json` | Bookmarks, streaks, connector credentials |
| `secrets` | Cryptographically secure random topic IDs for ntfy.sh |
| `threading` | Parallel connector dispatch |
| `signal` | Daemon process management (SIGTERM) |
| `os` | Double-fork daemonization (Unix) |
| `re` | Arabic text processing, surah name matching |

---

## Data Sources (No Installation Required)

These are external services the CLI talks to — all free, open, no API key:

| Service | URL | Used for |
|---|---|---|
| **AlQuran.cloud** | `api.alquran.cloud/v1/` | Quran text in 90+ translations |
| **ip-api.com** | `ip-api.com/json/` | Auto location detection |
| **fawazahmed0/hadith-api** | `cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/` | Sahih hadith corpus |
| **ntfy.sh** | `ntfy.sh/{topic}` | Free phone push notifications |

---

## Install Commands

```bash
# Minimal (reading, prayer times, schedule, Ramadan, Eid)
pip install quran-cli

# With AI guide
pip install "quran-cli[ai]"

# With all connectors (Telegram, WhatsApp)
pip install "quran-cli[connectors]"

# Full installation (everything)
pip install "quran-cli[all]"

# Development
pip install "quran-cli[dev]"
```

---

## Platform Notes

| Platform | Notes |
|---|---|
| **Linux** | Full support. Daemon uses systemd-compatible double-fork. Desktop notifications via libnotify. |
| **macOS** | Full support. Daemon uses `os.fork()`. Desktop notifications via osascript. |
| **Windows** | Full support. Daemon runs inline (no fork). Desktop notifications via Windows Toast API via plyer. |
| **Termux (Android)** | Partial — prayer times, reading, Ramadan all work. No desktop notifications. |
| **Docker** | Prayer times + reading work. No desktop notifications. Phone push (ntfy.sh) works. |

---

## Disk Space

| Item | Size |
|---|---|
| Package itself | ~350 KB |
| Quran SQLite cache (all surahs, 1 language) | ~3 MB |
| Quran SQLite cache (all surahs, all 13 languages) | ~35 MB |
| RAG corpus (SQLite, Quran + Hadith) | ~2 MB |
| Config + state files | <50 KB |

---

## Network Requirements

| Feature | Network needed? |
|---|---|
| Reading (after first fetch) | Offline ✓ |
| Prayer times | Offline ✓ (pure calculation) |
| Schedule / Ramadan / Eid | Offline ✓ |
| First-time surah fetch | Online (AlQuran.cloud) |
| Quran search (live) | Online (AlQuran.cloud) |
| Quran search (cached) | Offline ✓ |
| RAG corpus seeding | Online (first run only) |
| AI guide answers | Online (ANTHROPIC_API_KEY) |
| Auto location detect | Online (ip-api.com) |
| ntfy.sh notifications | Online (push only) |
| Telegram/WhatsApp | Online |
| News | Online (RSS feeds) |
