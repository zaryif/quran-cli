# 🚀 quran-cli — Upcoming Features (Soon™)

> **v1.1.8 shipped on Eid 🌙 — here's what's next.**

---

## ✅ Everything Announced Is Live

| Feature | Status | Where |
|---------|--------|-------|
| Offline Quran with 13 translations | ✅ Shipped | `quran read`, `quran_engine.py` |
| Interactive terminal dashboard | ✅ Shipped | `quran gui`, `gui.py` |
| Prayer schedules (auto-location) | ✅ Shipped | `quran pray`, `quran schedule` |
| Dynamic countdowns | ✅ Shipped | `quran pray next` |
| Rakat information | ✅ Shipped | `quran namaz` |
| AI Guide (RAG: Quran + Hadith) | ✅ Shipped | `quran guide` |
| Telegram notifications | ✅ Shipped | `quran connect telegram` |
| Gmail notifications | ✅ Shipped | `quran connect gmail` |
| WhatsApp (Twilio) | ✅ Shipped | `quran connect whatsapp` |
| ntfy.sh phone push | ✅ Shipped | `quran connect ntfy` |
| Webhook (Discord/Slack) | ✅ Shipped | `quran connect webhook` |
| Ramadan tracking + progress bar | ✅ Shipped | `quran ramadan` |
| Randomized splash Ayah | ✅ Shipped | `quran gui` splash screen |
| Bookmarks | ✅ Shipped | `quran bookmark` |
| Tafsir | ✅ Shipped | `quran tafsir` |
| Reading/fasting streak | ✅ Shipped | `quran streak` |

---

## 🔜 Coming Next — v1.2.x Roadmap

### 1. 🔊 Audio Recitation Playback
Play famous reciters (Mishary, Sudais, Maher Al-Muaiqly) directly in the terminal.
```
quran read 36 --audio          # play audio while reading
quran read 2:255 --reciter sudais
```
**Why**: The Quran is meant to be heard. Terminal audio playback makes this complete.

---

### 2. 📅 Hijri Calendar & Islamic Events
Full Hijri calendar with upcoming Islamic events, milestones, and recommended fasts.
```
quran calendar                 # this month in Hijri
quran calendar --events        # upcoming Islamic dates
quran events                   # Shab-e-Meraj, Shab-e-Barat, etc.
```
**Why**: Currently `quran info hijri` shows today's date, but there's no calendar view or event awareness.

---

### 3. 🧮 Daily Dhikr Counter
Track and count daily adhkar — SubhanAllah, Alhamdulillah, Allahu Akbar — with a terminal-native counter.
```
quran dhikr                    # interactive counter
quran dhikr --tasbih 33        # count 33× SubhanAllah
quran dhikr stats              # daily/weekly dhikr history
```
**Why**: Dhikr is a core daily practice with no CLI tool available.

---

### 4. 🤲 Du'a Collection
Curated, searchable collection of authentic du'as from Quran and Sunnah, categorized by occasion.
```
quran dua morning              # morning adhkar
quran dua travel               # travel du'as
quran dua --search "protection"
```
**Why**: Du'as are always needed and currently only shown in `namaz` context.

---

### 5. 📊 Khatm (Quran Completion) Tracker
Track progress toward completing the entire Quran, with a Juz-by-Juz breakdown.
```
quran khatm                    # show progress
quran khatm mark 15            # mark Juz 15 complete
quran khatm --plan 30days      # auto-assign daily reading plan
```
**Why**: Many users aim to finish the Quran in a month (especially Ramadan). The streak tracker exists but doesn't track Khatm.

---

### 6. 🌐 Multi-Device Sync
Sync bookmarks, reading progress, and streaks across machines using a lightweight cloud backend or Git-based sync.
```
quran sync setup               # link devices
quran sync push                # push local state
quran sync pull                # pull remote state
```
**Why**: Developers use multiple machines. Reading state should follow them.

---

### 7. 📱 Adhan Sound Playback
Play the Adhan call audibly at prayer times when the reminder daemon is running.
```
quran remind set --adhan       # enable adhan sound
quran remind set --no-adhan    # disable
```
**Why**: The config flag `adhan_sound` exists in `remind.py` but actual audio playback is not yet wired up.

---

### 8. 🧠 Smarter AI Guide — Conversation Memory
Currently each `quran guide` query is stateless. Add session memory so the AI can reference previous questions in `--interactive` mode.
```
quran guide --interactive      # multi-turn with memory
quran guide history            # review past Q&A
```
**Why**: The interactive mode works but has no memory between exchanges. Adding context would deepen conversations.

---

### 9. 📖 Juz / Para Navigation
Browse and read by Juz (Para) number — common organizational unit for the Quran.
```
quran read --juz 30            # read Juz Amma
quran info juz                 # list all 30 Juz with surah ranges
```
**Why**: Currently reading is surah-based only. Many readers think in Juz units.

---

### 10. 🏆 Community Leaderboard (opt-in)
Optional, privacy-first leaderboard for reading streaks and Khatm completions within a private group.
```
quran community join <group>
quran community board
```
**Why**: Accountability and friendly competition motivate consistent reading.

---

## 💡 Contribute

**All contributions welcome!** If any of these features excite you:

1. Fork the repo: [github.com/zaryif/quran-cli](https://github.com/zaryif/quran-cli)
2. Pick a feature from this list
3. Open a PR — even small steps count

```
python3 -m pip install git+https://github.com/zaryif/quran-cli.git
```

**Eid Mubarak from the quran-cli community! 🌙**
