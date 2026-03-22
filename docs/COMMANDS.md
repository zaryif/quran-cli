# quran-cli Command Reference
> Complete guide to every command, flag, and option. v1.2.6

---

## Global options

```bash
quran --help          # full command list
quran --version       # show version
quran --install-completion  # install shell autocomplete
```

---

## quran (default — no subcommand)

Running `quran` with no arguments shows the interactive dashboard.

```bash
$ quran
```

---

## quran gui

Interactive arrow-key dashboard (same as bare `quran`).

```bash
quran gui
```

Menu options: Read Quran · Read with Translation · Search · Daily Prayer Schedule ·
Ramadan Guide · Prayer Details · Eid Guide · Browse Hadith · Muslim World News ·
Reading Streak · Bookmarks · Change Language · Notification Channels · AI Guide ·
All Commands · Run Command · Update quran-cli

---

## quran schedule

**The flagship view.** Full-day Islamic schedule with live progress bars.
Auto-detects Ramadan and adds Sehri, Iftar, Tarawih rows.

```bash
quran schedule                      # today's full schedule (default view)
quran schedule --week               # 7-day prayer timetable
quran schedule --date 2026-03-25    # schedule for a specific date
```

**Output columns:** Prayer name · Time · Progress bar (████░░░░) · Status (▶ next / ✓ done / —)

---

## quran pray

Prayer times and setup.

```bash
quran pray                          # today's 5 prayer times + location
quran pray next                     # countdown panel to next prayer
quran pray setup                    # interactive: location + method wizard
```

**Supported calculation methods:**
`Karachi` · `ISNA` · `MWL` · `Makkah` · `Egypt` · `Turkey` · `Singapore` · `Tehran`

**Asr methods:** `Standard` (Shafi/Maliki/Hanbali) · `Hanafi`

---

## quran read

Read Quran text with translation and Arabic.

```bash
quran read 1                        # full Surah Al-Fatihah
quran read 2:255                    # single ayah (Ayat ul-Kursi)
quran read 2:1-10                   # ayah range
quran read 36                       # Surah Ya-Sin (full)
quran read 36 --lang bn             # Bangla translation
quran read 18 --dual                # Arabic + primary translation side by side
quran read 18 --dual2               # primary + secondary (lang2) side by side
quran read 18 --dual2 --lang en --lang2 bn  # explicit two-language mode
quran read 2 --no-arabic            # translation only
quran read 67 --lang ur             # Urdu (Jalandhry)
```

**Language codes:** `en` · `bn` · `ar` · `ur` · `tr` · `fr` · `id` · `ru` · `de` · `es` · `zh` · `nl` · `ms`

---

## quran search

Full-text search across all cached Quran text.

```bash
quran search "patience"             # search in default language
quran search "sabr"                 # Arabic keyword
quran search "light" --lang en
quran search "رحمة" --lang ar
quran search "tawakkul" --limit 5
```

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

## quran hadith  *(new in v1.2.6)*

Browse and search authentic Hadith from the Kutub al-Sittah.
All data from fawazahmed0/hadith-api (free CDN, no API key).
Only Sahih and Hasan grade hadith.

```bash
quran hadith                        # interactive topic picker
quran hadith daily                  # today's hadith of the day (rotates daily)
quran hadith topics                 # list all 19 topic categories
quran hadith search "patience"      # search by topic keyword
quran hadith search "tawakkul"      # search for reliance on Allah
quran hadith read bukhari 1 1       # read a specific hadith
quran hadith read muslim 6 38       # Sahih Muslim on patience
quran hadith read tirmidhi 27 1     # Jami at-Tirmidhi on tawakkul
```

**Available topic categories:**
`intention` · `prayer` · `fasting` · `quran` · `pillars` · `friday` ·
`laylatul-qadr` · `parents` · `consistency` · `kindness` · `patience` ·
`charity` · `brotherhood` · `dua` · `wudu` · `dhikr` · `tawakkul` ·
`knowledge` · `repentance`

**Collections:**
| Key | Full Name |
|---|---|
| `bukhari` | Sahih Bukhari |
| `muslim` | Sahih Muslim |
| `abudawud` | Abu Dawud |
| `tirmidhi` | Jami at-Tirmidhi |
| `nasai` | Sunan an-Nasa'i |
| `ibnmajah` | Sunan Ibn Majah |

---

## quran guide  *(AI-powered)*

Ask questions answered from Quran and authentic Hadith.

```bash
quran guide "how to perform wudu"
quran guide "what does the Quran say about patience"
quran guide --hadith "virtues of Salah"
quran guide --quran "signs of the Day of Judgement"
quran guide --interactive                  # multi-turn chat mode
quran guide --offline "what is tawakkul"  # BM25 search, no API
```

**Requirements:** `ANTHROPIC_API_KEY` environment variable for AI mode. Offline mode works without API key.

---

## quran ramadan

Ramadan timings, calendar, and fast tracker.

```bash
quran ramadan                       # today's sehri, iftar, tarawih + fast progress
quran ramadan --week                # 7-day sehri/iftar table
quran ramadan --month               # full 30-day Ramadan calendar
quran ramadan --fast                # mark today's fast as complete (streak++)
```

Output includes: Sehri end time · Iftar time · Tarawih time · Fast duration ·
Laylatul Qadr nights highlighted (21, 23, 25, 27, 29)

---

## quran eid

Complete Eid guide — Eid ul-Fitr and Eid ul-Adha.

```bash
quran eid                           # next Eid overview + dates
quran eid fitr                      # Eid ul-Fitr salah guide (9 steps)
quran eid adha                      # Eid ul-Adha + Qurbani guide
quran eid --takbeer                 # Takbeer text (Arabic + transliteration)
```

---

## quran namaz

Deep guide for performing each prayer.

```bash
quran namaz                         # interactive prayer picker
quran namaz fajr
quran namaz dhuhr
quran namaz asr
quran namaz maghrib
quran namaz isha
quran namaz witr                    # Witr guide with Qunoot
quran namaz jummah                  # Friday prayer guide
quran namaz tarawih                 # Tarawih (Ramadan) guide
```

Output per prayer: Arabic name · Time today · Rakah breakdown (Sunnah/Fard/Nafl) ·
Color-coded rakah dots · Significance · Common mistakes · Du'a

---

## quran remind

Manage the background reminder daemon.

```bash
quran remind on                     # start daemon
quran remind off                    # stop daemon
quran remind status                 # show status + settings
quran remind set --goal 5ayah       # set daily reading goal
quran remind set --at 20:00         # set reading reminder time
quran remind set --prayers fajr,asr # choose which prayers to notify
quran remind set --prayers all      # all 5 prayers
quran remind set --prayers none     # reading goal only
quran remind set --advance 15       # notify N minutes before prayer
quran remind phone                  # link phone via ntfy.sh (QR code)
quran remind test                   # send a test notification now
```

---

## quran connect

Set up notification channels for cross-device alerts.

```bash
quran connect list                  # show all channels + status
quran connect telegram              # setup Telegram push notifications
quran connect whatsapp              # setup WhatsApp (Twilio)
quran connect gmail                 # setup Gmail reminder digest
quran connect ntfy                  # link phone via ntfy.sh (free, QR)
quran connect webhook <url>         # Discord, Slack, Home Assistant
quran connect test telegram         # send test notification
quran connect verify                # test all enabled channels at once
quran connect off telegram          # disable a channel
quran connect on  telegram          # re-enable a channel
```

---

## quran bot  *(new in v1.2.6)*

Standalone Telegram prayer reminder bot. Free via Telegram Bot API.
Users subscribe with `/start` in the bot, receive all 5 prayer times
plus Ramadan and Laylatul Qadr alerts.

```bash
quran bot setup                     # step-by-step BotFather guide
quran bot start                     # start the bot (runs in foreground)
quran bot start --token <token>     # start with explicit token
quran bot status                    # check bot configuration
```

**Telegram bot commands (for end users):**
```
/start          subscribe + show welcome
/pray           today's prayer times
/schedule       full day schedule
/ramadan        Ramadan sehri/iftar timings
/ayah           random ayah
/hadith         hadith of the day
/settings       how to change location/method
/setlocation    /setlocation Dhaka or /setlocation 23.81,90.41
/setmethod      /setmethod Karachi
/stop           unsubscribe
```

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

## quran cache

Download Quran translations for fully offline use.

```bash
quran cache                         # show what's currently cached
quran cache download                # interactive: pick languages, download
quran cache download --all          # download all 13 languages
quran cache download --lang bn      # download a single language
quran cache clear                   # delete cache to free disk space
```

---

## quran config

View and update all settings.

```bash
quran config show                   # show all settings
quran config set lang bn            # set primary language
quran config set lang2 ur           # set secondary (splash screen) language
quran config set method Karachi     # prayer calculation method
quran config set asr_method Hanafi  # Asr calculation (Standard or Hanafi)
quran config set location auto      # re-run IP geolocation
quran config set location.city Dhaka
quran config set location.lat 23.8103
quran config set location.lon 90.4125
quran config set remind.goal_ayahs 10
quran config set remind.goal_time 21:00
quran config set remind.advance_min 15
quran config set ramadan.notify_sehri_min 20
quran config set ramadan.notify_iftar_min 10
quran config set display.arabic true
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

## quran update

Update to the latest version from GitHub.

```bash
quran update
```

---

## Shell integration

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Show daily ayah on new terminal
quran quote 2>/dev/null

# Show next prayer in prompt (PS1)
export PS1='$(quran pray next --short 2>/dev/null) \$ '

# Quick aliases
alias qs='quran schedule'
alias qp='quran pray next'
alias qr='quran read'
alias qh='quran hadith daily'
```

---

## Environment variables

```bash
ANTHROPIC_API_KEY=sk-ant-...        # enables quran guide AI mode
TELEGRAM_BOT_TOKEN=123:ABC...       # enables quran bot start without config
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
quran --install-completion bash
quran --install-completion zsh
quran --install-completion fish
```
