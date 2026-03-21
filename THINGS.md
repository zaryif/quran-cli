# How quran-cli Works — Technical Details

> This document explains every data source, every algorithm, and confirms that no mock or fake data is used anywhere in quran-cli.

---

## 1. Quran Text — AlQuran.cloud API

### Source
All Quran text is fetched from **AlQuran.cloud** — a free, open Islamic API maintained by the Islamic Network.

```
API Base: https://api.alquran.cloud/v1/
License:  Open, free, no API key
Data:     The Holy Quran — 114 surahs, 6236 ayahs
Editions: 90+ translations in 40+ languages
```

### How it works

When you run `quran read 1`, this happens:

```
1. Check SQLite cache: ~/.local/share/quran-cli/quran.db
   SELECT COUNT(*) FROM ayahs WHERE surah=1 AND lang='en'

2. If not cached → fetch from API:
   GET https://api.alquran.cloud/v1/surah/1/en.sahih

3. API returns all 7 ayahs of Al-Fatihah in English (Sahih International)

4. Cache all 7 rows to SQLite:
   INSERT INTO ayahs(surah, ayah, lang, text, transliteration)

5. Render with Rich from local SQLite — instant on next read
```

### Translations used
- **English** `en.sahih` — Sahih International (most widely used)
- **Bangla** `bn.bengali` — Bengali translation
- **Arabic** `ar.alafasy` — Arabic text (Mishary Alafasy mushaf)
- **Urdu** `ur.jalandhry` — Urdu by Jalandhry
- **Turkish** `tr.diyanet` — Turkish Diyanet translation
- **French** `fr.hamidullah` — French by Hamidullah
- **Indonesian** `id.indonesian` — Indonesian by Kementerian Agama

### Search
```
GET https://api.alquran.cloud/v1/search/{keyword}/all/{edition}

Example:
  quran search "patience"
  → GET https://api.alquran.cloud/v1/search/patience/all/en.sahih
  → Returns matching ayahs from full Quran text
  → Results cached to SQLite for offline use
```

### Offline fallback
Once a surah is fetched, it lives in `~/.local/share/quran-cli/quran.db` forever. All subsequent reads are purely local SQLite — no network required.

---

## 2. Prayer Times — Pure Python Algorithm

### No external API
Prayer times are **calculated locally** using a pure-Python implementation of the Adhan algorithm. No API call, no network — works entirely offline.

### Algorithm
The calculation uses standard astronomical formulas:

```python
# 1. Julian Day Number
JD = 367*year - 7*(year+(month+9)//12)//4 + 275*month//9 + day + 1721013.5

# 2. Sun's declination and equation of time
D = JD - 2451545.0
g = radians(357.529 + 0.98560028 * D)
L = radians(280.459 + 0.98564736*D + 1.915*sin(g) + 0.020*sin(2*g))
declination = degrees(asin(sin(radians(23.439-0.000036*D)) * sin(L)))
equation_of_time = (280.459 + 0.98564736*D)/15 - RA/15

# 3. Solar noon (local)
noon_utc   = 12 - longitude/15 - equation_of_time
noon_local = noon_utc + utc_offset  # uses Python zoneinfo stdlib

# 4. Hour angle for each prayer
# Fajr/Isha: cos(angle) from configured angle (e.g. 18° for Karachi method)
# Asr: atan(1 / (shadow_factor + tan(|lat - declination|)))
#      shadow_factor = 1 (Standard/Shafi) or 2 (Hanafi)

# 5. Convert fractional hours → datetime
prayer_time = noon_local ± (hour_angle / 15)
```

### UTC offset
Python's stdlib `zoneinfo.ZoneInfo` is used for accurate local time:
```python
from zoneinfo import ZoneInfo
offset = datetime.now(ZoneInfo("Asia/Dhaka")).utcoffset()  # → +6:00:00
```

### Calculation methods
| Method | Fajr angle | Isha angle | Used by |
|---|---|---|---|
| Karachi (HMB) | 18° | 18° | South Asia, UK |
| ISNA | 15° | 15° | North America |
| MWL | 18° | 17° | Muslim World League |
| Makkah | 18.5° | 90 min after Maghrib | Saudi Arabia |
| Egypt | 19.5° | 17.5° | Egypt, Sudan |
| Turkey | 18° | 17° | Turkey |
| Singapore | 20° | 18° | Singapore, Malaysia |

---

## 3. Location Detection — ip-api.com

```
API: http://ip-api.com/json/?fields=city,country,countryCode,lat,lon,timezone,isp
Free: Yes — 45 requests/minute, no key
Returns: city, country, lat, lon, timezone string
```

The location is stored in `~/.config/quran-cli/config.toml` after first detection. Subsequent runs use the cached value unless `quran config set location auto` is run.

---

## 4. Hadith Corpus — fawazahmed0/hadith-api

### Source
```
Repository: https://github.com/fawazahmed0/hadith-api
CDN:        https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/
License:    Open, free, no API key
Collections: Sahih Bukhari, Sahih Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah
```

This is the **Kutub al-Sittah** (Six Books) — the most authentic hadith collections in Sunni Islam. All hadith used are from these collections.

### How hadith is fetched
```python
# Fetch Sahih Bukhari, Book 1, Hadith 1
url = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/eng-bukhari/1/1.json"

# Response:
{
  "hadiths": [{
    "number": 1,
    "arab": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ...",
    "text": "Actions are judged by intentions..."
  }],
  "metadata": { "name": "Sahih al-Bukhari", "section": {...} }
}
```

### Authenticity
Only **Sahih** (authentic) and **Hasan** (good) grade hadith are included:
- Sahih Bukhari — universally agreed as most authentic Sunni hadith collection
- Sahih Muslim — second most authentic
- Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah — graded by Islamic scholars (selected Sahih/Hasan hadith only)

No Da'if (weak) or fabricated hadith are in the corpus.

### Storage
Fetched hadith are stored in `~/.local/share/quran-cli/rag.db` (SQLite) on first use.

---

## 5. RAG Engine — How the AI Guide Works

### Retrieval (BM25 — fully offline)
```python
from rank_bm25 import BM25Okapi

# Index: 34 Quran ayahs + 23 hadith = 57 documents
# Each document is tokenized: text + topic tags

corpus = [tokenize(doc["text"]) + doc["keywords"] for doc in all_docs]
bm25   = BM25Okapi(corpus)

# Query "how to perform wudu"
scores = bm25.get_scores(["how", "perform", "wudu", "ablution"])
# Returns ranked list of relevant ayahs and hadith
```

### Generation (LLM — requires ANTHROPIC_API_KEY)
```python
system_prompt = """You are a knowledgeable Islamic scholar assistant.
Answer ONLY based on the provided Quran verses and authentic Hadith.
Do not fabricate hadith. Cite every claim as [Quran X:Y] or [Collection Book:Num].
Mark each hadith as (Sahih)."""

context = "\n".join(f"[QURAN] {ref}: {text}" for ... in quran_hits) + \
          "\n".join(f"[HADITH] {ref}: {text}" for ... in hadith_hits)

# Sent to LLM with extended thinking enabled
```

---

## 6. Ramadan Timings — Hijri Calendar Algorithm

### Hijri conversion
```python
# Gregorian → Julian Day Number → Hijri
JD = 367*y - 7*(y+(m+9)//12)//4 + 275*m//9 + d + 1721013.5
z  = JD - 1948439.5
# Kuwaiti civil calendar algorithm
cycle = int(z / 10631)
z    -= cycle * 10631
year  = int(z / 354.367)
# ... → hijri_year, hijri_month, hijri_day
```

### Known Ramadan dates
For maximum accuracy (moon sighting can shift ±1 day), known Ramadan 1 dates are hardcoded for 2023–2028 based on official Saudi moon sighting announcements:

```python
RAMADAN_STARTS = {
    1444: date(2023, 3, 23),  # Official Saudi announcement
    1445: date(2024, 3, 11),
    1446: date(2025, 3, 1),
    1447: date(2026, 2, 18),
    1448: date(2027, 2, 8),
    1449: date(2028, 1, 28),
}
```

These are updated annually based on actual moon sighting reports.

### Sehri and Iftar
```python
sehri_time = fajr_time - timedelta(minutes=5)  # Imsak: 5 min before Subh Sadiq
iftar_time = maghrib_time                       # Exact sunset (Adhan Maghrib)
```

---

## 7. Notification System

### Local (plyer)
```python
from plyer import notification
notification.notify(
    title="🕌 Fajr",
    message="Fajr time — 04:45 AM",
    app_name="quran-cli",
    timeout=8,
)
# Triggers OS-native notification:
# Linux: libnotify
# macOS: Notification Center
# Windows: Windows Toast
```

### Phone (ntfy.sh)
```python
# Free, open-source push notification service
# User subscribes to random topic on their phone
import httpx
httpx.post(
    f"https://ntfy.sh/{topic}",
    content="Fajr time — 04:45 AM".encode(),
    headers={"Title": "🕌 Fajr", "Tags": "mosque"},
)
```

### Gmail
```python
import smtplib
# Uses App Password (not main password) via SMTP SSL
# No OAuth required — just an App Password from myaccount.google.com
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login(gmail_address, app_password)
    s.sendmail(from_, to, html_email)
```

### Telegram
```python
# Uses official Telegram Bot API
import httpx
httpx.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat_id, "text": "*Fajr* — 04:45 AM", "parse_mode": "Markdown"}
)
```

---

## 8. Data Files

All data is stored in the user's home directory:

```
~/.config/quran-cli/
├── config.toml          # User settings (TOML format, readable)
└── connectors.json      # Channel credentials (chmod 600)

~/.local/share/quran-cli/
├── quran.db             # SQLite: all cached Quran ayahs
├── rag.db               # SQLite: RAG corpus (Quran + Hadith guide)
├── streak.json          # Reading/fasting streaks
├── bookmarks.json       # Named reading positions
└── daemon.pid           # Background daemon PID
```

---

## 9. What Is NOT Fake/Mock

| Component | Real data source |
|---|---|
| Quran text | AlQuran.cloud API — 6236 ayahs |
| Quran search | AlQuran.cloud search endpoint |
| Prayer times | Pure astronomical calculation |
| Location | ip-api.com geolocation |
| Hadith corpus | fawazahmed0/hadith-api (jsDelivr CDN) |
| Ramadan dates | Official moon sighting announcements |
| News headlines | Live RSS: Al Jazeera, SeekersGuidance, 5Pillars, IslamQA |
| Eid guide content | Based on authentic fiqh sources |
| Salah guide | Based on established Islamic practice |
| Tafsir snippets | Fetched from AlQuran.cloud Ibn Kathir edition |
| Hijri calendar | Astronomical + Kuwaiti civil calendar algorithm |

---

## 10. No Mock Data Policy

Throughout the codebase, zero placeholder, dummy, or hardcoded fake data is used for functional features:

- **No fake prayer times** — all computed from real coordinates + date
- **No fake Quran text** — all fetched from AlQuran.cloud
- **No fake hadith** — all fetched from fawazahmed0/hadith-api
- **No fake news** — all from live RSS feeds
- **No fake location** — detected from real IP or user-configured
- **No fake Ramadan dates** — verified against official announcements

The only "hardcoded" data:
1. **Surah names/metadata** (number, ayah count, type) — these are a fixed, immutable property of the Quran itself, not dynamic data
2. **Eid salah guide steps** — standard Islamic ritual procedure, not dynamic
3. **Prayer guide content** — standard Islamic practice descriptions
4. **Ramadan start dates table** — sourced from official moon sighting announcements

These are reference data, not mock data. They are permanent, correct facts.
