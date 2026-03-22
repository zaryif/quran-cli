# Installation Guide

> **quran-cli** — Islamic terminal companion by [Md Zarif Azfar](https://mdzarifazfar.me)

---

## Requirements

- **Python 3.11+** — check with `python3 --version`
- **pip** — comes with Python
- Internet connection (first run only — for fetching Quran text)

---

## Quick Install

```bash
pip install quran-cli
```

> **macOS users:** Use `pip3` instead of `pip` and `python3` instead of `python`.
> macOS ships with Python 2 as `python` — the `pip`/`python` commands may point to
> the wrong version or not exist at all.
>
> ```bash
> pip3 install quran-cli
> ```

Then run:

```bash
quran
```

You'll see the splash screen and be ready to go.

---

## Install from GitHub (latest)

```bash
git clone https://github.com/zaryif/quran-cli.git
cd quran-cli
pip install -e .          # Linux / Windows
# pip3 install -e .       # macOS
quran
```

### **Running Locally (Manual / No Install)**
If the above commands fail, you can run the CLI directly from the source directory:

**macOS / Linux:**
```bash
export PYTHONPATH=.
python3 -m quran gui
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="."
$env:PYTHONIOENCODING="utf-8"
python -m quran gui
```

**Windows (Command Prompt):**
```cmd
set PYTHONPATH=.
set PYTHONIOENCODING=utf-8
python -m quran gui
```

---

## One-line installer

```bash
curl -fsSL https://raw.githubusercontent.com/zaryif/quran-cli/main/install.sh | bash
```

---

## Homebrew (macOS / Linux)

```bash
brew install zaryif/tap/quran-cli
quran
```

---

## First Run

```bash
# 1. Set up your location (auto-detects from IP)
quran pray setup

# 2. See today's full schedule
quran schedule

# 3. Read Al-Fatihah
quran read 1

# 4. Read by name
quran read kahf

# 5. Set your language (optional — default is English)
quran config set lang bn     # Bangla
quran config set lang ur     # Urdu
quran config set lang ar     # Arabic
```

---

## Optional Features

### AI Guide (Quran + Hadith answers)

```bash
pip install "quran-cli[ai]"            # pip3 on macOS
export ANTHROPIC_API_KEY=sk-ant-...    # get at console.anthropic.com
quran guide "what does the Quran say about patience"
```

### Telegram / WhatsApp Notifications

```bash
pip install "quran-cli[connectors]"    # pip3 on macOS
quran connect telegram      # follow setup wizard
quran connect whatsapp      # follow setup wizard
```

### Everything

```bash
pip install "quran-cli[all]"           # pip3 on macOS
```

---

## Enable Phone Notifications (Free — no account)

```bash
quran connect ntfy          # shows QR code
# Install ntfy app → subscribe to your topic → done
quran remind on             # start background daemon
```

---

## Shell Integration

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Daily ayah on every new terminal
quran quote 2>/dev/null

# Quick aliases
alias qs='quran schedule'
alias qp='quran pray next'
alias qr='quran ramadan'
```

---

## Supported Platforms

| Platform | Support |
|---|---|
| Linux (Ubuntu, Debian, Arch, Fedora) | ✅ Full |
| macOS 12+ | ✅ Full |
| Windows 10/11 (PowerShell / WSL) | ✅ Full |
| Android (Termux) | ⚡ Partial (no desktop notifications) |
| Docker | ⚡ Partial (no desktop notifications) |

---

## Uninstall

```bash
pip uninstall quran-cli         # pip3 on macOS
rm -rf ~/.config/quran-cli     # remove settings
rm -rf ~/.local/share/quran-cli  # remove cached data
```

---

## Troubleshooting

**`quran: command not found`**
```bash
# Make sure pip's bin directory is in PATH
export PATH="$HOME/.local/bin:$PATH"
# Add this line to ~/.bashrc or ~/.zshrc

# macOS: if installed with pip3, the binary may be at:
export PATH="$(python3 -m site --user-base)/bin:$PATH"

# Windows: Use "python -m quran" instead
# If "quran" is not recognized, the "python -m quran" method is the most reliable way 
# to run the application across different Windows shell environments.
```

**Arabic text renders incorrectly**
```bash
pip install arabic-reshaper python-bidi
# Use a font with Arabic support: Noto Sans Arabic, Cascadia Code, etc.
```

**Prayer times seem off**
```bash
quran pray setup        # re-run location setup
quran config set method Karachi   # or ISNA, MWL, Makkah, etc.
quran config set asr_method Hanafi  # if you follow Hanafi madhab
```

**Notifications not appearing**
```bash
quran remind status     # check daemon status
quran remind on         # restart daemon
quran connect desktop   # verify plyer is working
```

**`No module named 'httpx'`**
```bash
pip install httpx       # or: pip install quran-cli --upgrade
# macOS: pip3 install httpx
```

---

## Configuration

Config file lives at `~/.config/quran-cli/config.toml` — you can edit it directly:

```toml
lang = "bn"                # your preferred language
method = "Karachi"         # prayer calculation method
asr_method = "Standard"    # or Hanafi

[location]
city = "Dhaka"
country = "BD"
lat = 23.8103
lon = 90.4125
tz = "Asia/Dhaka"
auto = true               # re-detect location on each run

[remind]
enabled = true
goal_ayahs = 5
goal_time = "20:00"
phone_topic = ""          # set by: quran connect ntfy

[ramadan]
notify_sehri_min = 15     # warn 15 min before sehri ends
notify_iftar_min = 10     # warn 10 min before iftar
```

---

## All Commands at a Glance

```
quran                       welcome splash screen
quran schedule              full day schedule (prayer + Ramadan)
quran schedule --week       7-day timetable
quran pray                  today's 5 prayer times
quran pray next             countdown to next prayer
quran pray setup            location + method wizard
quran read <surah>          read by number: quran read 18
quran read <name>           read by name: quran read kahf
quran read <ref>            read by ayah: quran read 2:255
quran read <ref> --dual     Arabic + translation
quran read <ref> --lang bn  specific language
quran search "patience"     search the Quran
quran tafsir 2:255          Ibn Kathir tafsir
quran quote                 daily ayah
quran namaz fajr            how to perform Fajr
quran namaz jummah          Friday prayer guide
quran ramadan               today's sehri, iftar, tarawih
quran ramadan --month       30-day Ramadan calendar
quran eid                   upcoming Eid dates
quran eid fitr              Eid ul-Fitr salah guide
quran eid adha              Eid ul-Adha + Qurbani guide
quran guide "..."           AI Quran + Hadith guide
quran guide --interactive   multi-turn chat
quran connect list          all notification channels
quran connect telegram      setup Telegram bot
quran connect ntfy          link phone (free QR)
quran connect gmail         setup Gmail digest
quran remind on             start notification daemon
quran streak                reading + fasting streaks
quran bookmark save "x" 2:255  save position
quran news                  Muslim world headlines
quran info surahs           list all 114 surahs
quran info hijri            today's Hijri date
quran config show           view all settings
quran config set lang bn    change language
```

---

## Built by

**Md Zarif Azfar** — [mdzarifazfar.me](https://mdzarifazfar.me) · [github.com/zaryif](https://github.com/zaryif)

A developer from Dhaka, Bangladesh. Built this because the terminal is where I live, and it needed an Islamic companion.

*بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ*
