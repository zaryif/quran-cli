# About quran-cli

## Who made this?

**quran-cli** was built by **Md Zarif Azfar** — a developer and Muslim from Bangladesh.

The project grew out of a simple frustration: too many beautiful Quran apps exist for phones, but the terminal — where developers spend most of their day — has nothing.
- 🕌 **Prayer Reminders & Daemon:** Background notifications for 5 daily prayers with an interactive setup wizard (`quran remind setup`).
- 🌙 **Ramadan & Fasting Alerts:** Automatic alerts for Sahur and Iftar timings, usable year-round.
- 📱 **Cross-platform Push:** Native macOS/Windows/Linux popups + Telegram & phone (ntfy) integration.
So I built quran-cli to fill that gap.

---

## Zarif Azfar

I'm a developer based in **Dhaka, Bangladesh**. I work primarily in Python and build tools that I actually use every day. quran-cli is one of them — it's open on my terminal from Fajr to Isha.

**Links:**
- Website: [mdzarifazfar.me](https://mdzarifazfar.me)
- GitHub: [github.com/zaryif](https://github.com/zaryif)

---

## Why I built this

The terminal is where I live. And as a Muslim, my day is structured around prayer times, Quran reading, and — during Ramadan — sehri and iftar. Every existing solution required opening a phone app, a browser, or some heavy GUI.

I wanted:
- Fajr time in my terminal prompt
- `quran read kahf` on a Friday morning
- Sehri warning 15 minutes before Fajr — without touching my phone
- Proper Arabic rendering in the terminal
- A way to ask "what does the Quran say about patience" and get a cited, grounded answer

quran-cli is the answer to all of those.

---

## Design philosophy

**Clean, minimal, intentional.** The terminal is not a place for clutter. Every command should do exactly one thing well. The aesthetic is borrowed from tools I love — `git`, `gh`, `fd`, `bat` — monospaced, dark, purposeful.

**Offline-first.** Once you've fetched a surah, it lives in SQLite forever. Prayer times are pure computation — no network required. The tool works on a plane at 30,000 feet.

**Authentic data only.** No scraped data. No AI-generated Islamic content. Every Quran verse comes from AlQuran.cloud. Every hadith comes from the Kutub al-Sittah (the Six Books) via the fawazahmed0/hadith-api project, now featuring full structured book browsing.

---

## The stack

Built entirely in Python, using:

- **Typer** — clean CLI framework
- **Rich** — beautiful terminal output
- **Pure-Python Adhan** — prayer times without any third-party prayer library
- **AlQuran.cloud** — free, open Quran API (no key required)
- **fawazahmed0/hadith-api** — free, open hadith API (no key required)
- **BM25 (rank-bm25)** — fast offline search for the AI guide
- **ntfy.sh** — free, open-source phone push notifications

No vendor lock-in. No paid APIs. No accounts required for core functionality.

---

## Contributing

Contributions are welcome — especially:
- New language translations (`quran config set lang xx`)
- Bug fixes in prayer time edge cases (polar regions, etc.)
- New hadith topics for the guide corpus
- Translations of the CLI itself

Please open an issue or PR at [github.com/zaryif/quran-cli](https://github.com/zaryif/quran-cli).

---

## Acknowledgements

- **AlQuran.cloud** — for the open, free Quran API
- **fawazahmed0** — for the hadith-api project (the best free hadith resource online)
- **ip-api.com** — for the free IP geolocation API
- **ntfy.sh** — for free, open-source push notifications
- **The Rich and Typer teams** — for making beautiful terminal apps possible in Python
- Every Muslim developer who reviewed this and gave feedback

---

## License

MIT License — use freely, modify freely, distribute freely.

```
MIT License

Copyright (c) 2026 Md Zarif Azfar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

*بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ*

*In the name of Allah, the Most Gracious, the Most Merciful.*
