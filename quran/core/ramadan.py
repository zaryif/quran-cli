"""
Ramadan utilities — Hijri calendar, Ramadan detection, monthly timetable.
Uses a simple Hijri approximation (accurate ±1 day around moon sighting).
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Optional

# Known Ramadan 1 dates (Gregorian) for ±5 years — update yearly
RAMADAN_STARTS = {
    1444: date(2023, 3, 23),
    1445: date(2024, 3, 11),
    1446: date(2025, 3, 1),
    1447: date(2026, 2, 18),
    1448: date(2027, 2, 8),
    1449: date(2028, 1, 28),
}


def gregorian_to_hijri(g: date) -> tuple[int, int, int]:
    """Approximate Gregorian → Hijri conversion."""
    jd = (
        367 * g.year
        - (7 * (g.year + (g.month + 9) // 12)) // 4
        + (275 * g.month) // 9
        + g.day
        + 1721013.5
    )
    z  = jd - 1948439.5
    cy = int(z / 10631)
    z  -= cy * 10631
    j  = int(z / 354.367)
    z  -= int(j * 354.367)
    hm = int(z / 29.5) + 1
    hd = int(z - int((hm - 1) * 29.5)) + 1
    hy = cy * 30 + j + 1
    return hy, min(hm, 12), min(hd, 30)


def is_ramadan(d: Optional[date] = None) -> bool:
    d = d or date.today()
    _, hm, _ = gregorian_to_hijri(d)
    return hm == 9


def ramadan_day(d: Optional[date] = None) -> Optional[int]:
    d = d or date.today()
    hy, hm, hd = gregorian_to_hijri(d)
    if hm != 9:
        return None
    return hd


def ramadan_year(d: Optional[date] = None) -> int:
    d = d or date.today()
    hy, _, _ = gregorian_to_hijri(d)
    return hy


def ramadan_start_date(hijri_year: int) -> Optional[date]:
    return RAMADAN_STARTS.get(hijri_year)


def ramadan_end_date(hijri_year: int) -> Optional[date]:
    start = RAMADAN_STARTS.get(hijri_year)
    if start:
        return start + timedelta(days=29)  # 29 or 30 — use 29 (moon sighting)
    return None


def days_until_ramadan() -> Optional[int]:
    today = date.today()
    hy, hm, hd = gregorian_to_hijri(today)
    # Next Ramadan
    if hm < 9:
        next_hy = hy
    elif hm == 9:
        return 0
    else:
        next_hy = hy + 1
    start = RAMADAN_STARTS.get(next_hy)
    if start:
        return max(0, (start - today).days)
    return None


def monthly_timetable(lat: float, lon: float, hijri_year: int,
                      method: str = "Karachi",
                      asr_method: str = "Standard",
                      tz: str = "") -> list[dict]:
    """Generate full Ramadan month timetable."""
    from quran.core.prayer_times import get_prayer_times, sehri_time

    start = RAMADAN_STARTS.get(hijri_year)
    if not start:
        return []

    rows = []
    for i in range(30):
        d = start + timedelta(days=i)
        pt = get_prayer_times(lat, lon, for_date=d, method=method, asr_method=asr_method,
        tz=tz)
        rows.append({
            "day":     i + 1,
            "date":    d,
            "sehri":   sehri_time(pt),
            "fajr":    pt.fajr,
            "sunrise": pt.sunrise,
            "dhuhr":   pt.dhuhr,
            "asr":     pt.asr,
            "iftar":   pt.maghrib,
            "maghrib": pt.maghrib,
            "isha":    pt.isha,
            "tarawih": pt.isha.replace(
                hour=(pt.isha.hour + 1) % 24,
                minute=30
            ),
            "fast_duration_h": round(
                (pt.maghrib - sehri_time(pt)).total_seconds() / 3600, 2
            ),
        })
    return rows


LAYLATUL_QADR_NIGHTS = [21, 23, 25, 27, 29]
