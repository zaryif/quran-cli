# quran-cli Command Reference
> Complete guide to every command, flag, and option.

---

## Global options

```bash
quran --help          # full command list
quran --version       # show version
quran --install-completion  # install shell autocomplete
```

---

## quran (default — no subcommand)

Running `quran` with no arguments shows the welcome banner + quick-start hints.

```bash
$ quran
```

---

## quran schedule

**The flagship view.** Full-day Islamic schedule with live progress bars.
Auto-detects Ramadan and adds Sehri, Iftar, Tarawih rows.

```bash
quran schedule                      # today's full schedule (default view)
quran schedule --week               # 7-day prayer timetable
quran schedule --month              # full month (Ramadan: 30-day calendar)
quran schedule --date 2026-03-25    # schedule for a specific date
quran schedule --live               # live countdown, refreshes every second
quran schedule --normal             # force Normal mode (hide Ramadan rows)
quran schedule --ramadan            # force Ramadan mode (even outside Ramadan)
```

**Output columns:**
- Prayer name · Time · Progress bar (████░░░░) · Status (▶ next / ✓ done / —)

**Colors:**
- Green `▶` = next prayer
- Amber = Ramadan-specific rows (Sehri, Iftar, Tarawih)
- Dim = past prayers

---

## quran pray

Prayer times and setup.

```bash
quran pray                          # today's 5 prayer times + location
quran pray next                     # countdown panel to next prayer
quran pray setup                    # interactive: location + method wizard
quran pray --method ISNA            # override method for this session
quran pray --date 2026-04-01        # times for a different date
```

**Supported calculation methods:**
| Flag | Description | Region |
|---|---|---|
| `Karachi` | University of Islamic Sciences | South Asia, UK |
| `ISNA` | Islamic Society of North America | North America |
| `MWL` | Muslim World League | Europe, Far East |
| `Makkah` | Umm Al-Qura, Makkah | Saudi Arabia, Gulf |
| `Egypt` | Egyptian General Authority | Egypt, Sudan |
| `Turkey` | Diyanet İşleri Başkanlığı | Turkey |
| `Singapore` | MUIS | Singapore, Malaysia |

**Asr methods:**
- `Standard` — shadow = 1× object height (Shafi'i, Maliki, Hanbali)
- `Hanafi` — shadow = 2× object height (Hanafi madhab)

---

## quran read

Read Quran text with translation and Arabic.

```bash
quran read 1                        # full Surah Al-Fatihah
quran read 2:255                    # single ayah (Ayat ul-Kursi)
quran read 2:1-10                   # ayah range
quran read 36                       # Surah Ya-Sin (full)
quran read 36 --lang bn             # Bangla translation
quran read 18 --dual                # Arabic + English side by side
quran read 2 --no-arabic            # translation only
quran read 67 --lang ur             # Urdu (Jalandhry)
```

**Language codes:**
| Code | Language | Translator |
|---|---|---|
| `en` | English | Sahih International |
| `bn` | Bengali/Bangla | — |
| `ar` | Arabic | Original |
| `ur` | Urdu | Jalandhry |
| `tr` | Turkish | Diyanet |
| `fr` | French | Hamidullah |
| `id` | Indonesian | Kemenag |

---

## quran search

Full-text search across all cached Quran text.

```bash
quran search "patience"             # search in default language
quran search "sabr"                 # Arabic keyword
quran search "light and darkness" --lang en
quran search "رحمة" --lang ar       # Arabic full search
quran search "tawakkul" --limit 5   # limit results
```

> **Note:** Search works on cached surahs. Read a surah first to cache it.
> `quran read 1-114` will cache all surahs (takes a few minutes on first run).

---

## quran tafsir

Brief tafsir commentary for any ayah.

```bash
quran tafsir 2:255                  # Ayat ul-Kursi tafsir
quran tafsir 36:1-5                 # range tafsir
quran tafsir 1:1                    # Al-Fatihah opening
```

Source: Ibn Kathir (brief) via AlQuran.cloud API. Requires internet.

---

## quran guide  *(AI-powered)*

Ask questions answered from Quran and authentic Hadith.

```bash
quran guide "how to perform wudu"
quran guide "what does the Quran say about patience"
quran guide "sunnah acts on Friday"
quran guide "ruling on fasting for travelers"
quran guide --hadith "virtues of Salah"    # Hadith-focused search
quran guide --quran "signs of the Day of Judgement"
quran guide --interactive                  # multi-turn chat mode
quran guide --offline "what is tawakkul"  # BM25 search, no API
```

**How it works:**
1. Your question is matched against 6236 Quran ayahs + 900+ authentic hadith
2. Top-5 most relevant passages are retrieved (BM25 or semantic search)
3. Claude claude-sonnet-4-20250514 generates an answer grounded in those passages
4. Every claim is cited: `[Quran 2:186]` or `[Bukhari 8:395]`

**Authenticity policy:**
- Only Sahih and Hasan hadith in the corpus
- Da'if (weak) hadith clearly labelled if shown
- No unverified quotes

**Requirements:** `ANTHROPIC_API_KEY` environment variable for AI mode.
Offline mode works without API key.

---

## quran cache

Download Quran translations so you can read entirely offline without relying on the AlQuran.cloud API.

```bash
quran cache                         # view what languages and surahs are cached locally
quran cache download                # interactive prompt to select languages to cache
quran cache download --all          # download all 13 supported languages (114 surahs each)
quran cache clear                   # clear the local SQLite cache to free up disk space
```

> **Note:** The cache is automatically populated as you read `quran read`. This command just lets you pre-download everything all at once.

---

## quran ramadan

Ramadan timings, calendar, and fast tracker.

```bash
quran ramadan                       # today's sehri, iftar, tarawih + fast progress
quran ramadan --week                # 7-day sehri/iftar table
quran ramadan --month               # full 30-day Ramadan calendar
quran ramadan --notify              # show alert settings
quran ramadan --fast                # mark today's fast as complete (streak++)
quran ramadan --export csv          # export month to CSV
quran ramadan --export ical         # export to .ics calendar file
```

**When not in Ramadan:** shows countdown to next Ramadan.

---

## quran eid

Complete Eid guide — Eid ul-Fitr and Eid ul-Adha.

```bash
quran eid                           # next Eid overview + dates
quran eid fitr                      # Eid ul-Fitr salah guide (step by step)
quran eid adha                      # Eid ul-Adha + Qurbani guide
quran eid --takbeer                 # Takbeer text (Arabic + transliteration)
quran eid --countdown               # days until next Eid
```

**Eid ul-Fitr guide includes:**
- Sunnah acts before salah
- 9-step salah guide (including Khutbah protocol)
- Zakat ul-Fitr rules
- Takbeer text

**Eid ul-Adha guide includes:**
- 7-step sunnah checklist
- Salah guide
- Qurbani animal rules (Goat: 1, Cow/Camel: up to 7)
- Meat distribution: 1/3 · 1/3 · 1/3
- Takbeer al-Tashreeq (9th–13th Dhul Hijjah)

---

## quran namaz

Deep guide for performing each prayer.

```bash
quran namaz                         # interactive prayer details picker
quran namaz fajr                    # Fajr — rakah breakdown + description
quran namaz dhuhr
quran namaz asr
quran namaz maghrib
quran namaz isha
quran namaz witr                    # Witr prayer guide
quran namaz jummah                  # Jumu'ah (Friday) prayer guide
quran namaz tarawih                 # Tarawih (Ramadan) guide
```

**Output per prayer:**
- Arabic name + transliteration
- Time today (from your location)
- Rakah breakdown: Sunnah before · Fard · Sunnah after · Nafl
- Colour-coded rakah dots (filled = Fard, outline = Sunnah)
- Description of significance
- Common mistakes to avoid

---

## quran remind

Manage the background reminder daemon.

```bash
quran remind on                     # start daemon
quran remind off                    # stop daemon
quran remind status                 # show status + settings
quran remind set --goal 5ayah       # set daily reading goal
quran remind set --at 20:00         # set reading reminder time
quran remind set --prayers fajr,asr # choose which prayers to be reminded about
quran remind set --prayers all      # turn on reminders for all 5 prayers
quran remind set --prayers none     # only get the reading goal reminder
quran remind set --advance 15       # get phone/telegram push notifications 15 mins early
quran remind set --adhan on         # enable adhan sound
quran remind phone                  # link phone via ntfy.sh (QR code)
quran remind test                   # send a test notification now
```

---

## quran connect

Set up notification channels for cross-device alerts.

```bash
quran connect list                  # show all channels + status
quran connect telegram              # setup Telegram bot wizard
quran connect whatsapp              # setup WhatsApp (Twilio) wizard
quran connect gmail                 # setup Gmail reminder wizard
quran connect webhook <url>         # set custom webhook URL
quran connect test telegram         # send test notification to Telegram
quran connect test whatsapp
quran connect test gmail
quran connect off telegram          # disable a channel
quran connect on telegram           # re-enable a channel
```

**Notification triggers (all channels):**
- Prayer times (Fajr, Dhuhr, Asr, Maghrib, Isha)
- Sehri warning (configurable minutes before Fajr)
- Iftar time (Maghrib)
- Daily Quran reading goal reminder
- Ramadan special: Laylatul Qadr nights notification

---

## quran news

Muslim world news from curated RSS feeds.

```bash
quran news                          # top headlines (Al Jazeera default)
quran news --source seekers         # SeekersGuidance articles
quran news --source 5pillars        # 5Pillars UK
quran news --source islamqa         # IslamQA
quran news --limit 5                # limit results
```

---

## quran quote

Show daily ayah.

```bash
quran quote                         # today's daily ayah
quran quote --lang bn               # in Bangla
quran quote --random                # random ayah
```

---

## quran streak

Reading and fasting consistency tracker.

```bash
quran streak                        # show reading + fasting streaks
quran streak --reset reading        # reset reading streak
```

---

## quran bookmark

Save and navigate reading positions.

```bash
quran bookmark save "fajr" 18:1     # save position
quran bookmark save "last" 2:255 --note "Ayat ul-Kursi"
quran bookmark list                 # list all bookmarks
quran bookmark goto "fajr"          # jump to bookmark + continue reading
quran bookmark delete "fajr"        # delete bookmark
```

---

## quran config

View and update all settings.

```bash
quran config show                   # show all settings
quran config set lang bn            # set language
quran config set method Karachi     # prayer method
quran config set asr_method Hanafi  # Asr calculation
quran config set location auto      # re-run IP geolocation
quran config set location.city Dhaka
quran config set location.lat 23.8103
quran config set location.lon 90.4125
quran config set remind.goal_ayahs 10
quran config set remind.goal_time 21:00
quran config set ramadan.notify_sehri_min 20
quran config set ramadan.notify_iftar_min 10
quran config set display.arabic true
quran config set display.dual false
quran config set ai.enabled true
quran config set ai.embeddings bm25     # or sentence-transformers
quran config reset                  # reset all to defaults
quran config reset --yes            # skip confirmation
```

---

## quran info

Quick reference information.

```bash
quran info surahs                   # list all 114 surahs
quran info surah 36                 # details about Surah Ya-Sin
quran info methods                  # list prayer calculation methods
quran info languages                # list supported translation languages
quran info hijri                    # today's Hijri date
quran info location                 # show detected location
```

---

## Shell integration

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Show daily ayah on new terminal
quran quote 2>/dev/null

# Show next prayer in prompt (PS1)
export PS1='$(quran pray next --short 2>/dev/null) \$ '

# Alias for quick schedule
alias qs='quran schedule'
alias qp='quran pray next'
```

---

## Environment variables

```bash
ANTHROPIC_API_KEY=sk-ant-...        # enables quran guide AI mode
QURAN_CLI_CONFIG=/path/to/config    # override config directory
QURAN_CLI_DATA=/path/to/data        # override data directory
QURAN_CLI_DEBUG=1                   # verbose debug logging
QURAN_CLI_OFFLINE=1                 # force offline mode (no HTTP)
```

---

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Network error |
| 4 | Not found (surah, hadith, etc.) |

---

## Shell autocomplete

```bash
# Bash
quran --install-completion bash

# Zsh
quran --install-completion zsh

# Fish
quran --install-completion fish
```
