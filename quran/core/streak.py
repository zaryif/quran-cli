"""
Streak tracking — reading and fasting consistency, stored in JSON.
"""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path

STREAK_FILE = Path.home() / ".local" / "share" / "quran-cli" / "streak.json"


def _load() -> dict:
    if not STREAK_FILE.exists():
        return {
            "reading": {"last": None, "current": 0, "best": 0, "total_ayahs": 0},
            "fasting": {"last": None, "current": 0, "best": 0},
        }
    return json.loads(STREAK_FILE.read_text())


def _save(data: dict) -> None:
    STREAK_FILE.parent.mkdir(parents=True, exist_ok=True)
    STREAK_FILE.write_text(json.dumps(data, indent=2))


def mark_read(ayahs: int = 1) -> dict:
    data   = _load()
    today  = str(date.today())
    rd     = data["reading"]
    if rd["last"] == today:
        rd["total_ayahs"] += ayahs
    else:
        from datetime import datetime, timedelta
        yesterday = str(date.today() - timedelta(days=1))
        rd["current"] = rd["current"] + 1 if rd["last"] == yesterday else 1
        rd["best"]    = max(rd["best"], rd["current"])
        rd["last"]    = today
        rd["total_ayahs"] = rd.get("total_ayahs", 0) + ayahs
    _save(data)
    return data["reading"]


def mark_fast() -> dict:
    data  = _load()
    today = str(date.today())
    fd    = data["fasting"]
    if fd["last"] != today:
        from datetime import timedelta
        yesterday = str(date.today() - timedelta(days=1))
        fd["current"] = fd["current"] + 1 if fd["last"] == yesterday else 1
        fd["best"]    = max(fd["best"], fd["current"])
        fd["last"]    = today
    _save(data)
    return data["fasting"]


def get() -> dict:
    return _load()
