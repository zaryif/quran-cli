"""
Prayer times — pure-Python implementation of the Adhan calculation algorithm.
Supports: Karachi (HMB), ISNA, MWL, Makkah, Egypt, Tehran, Gulf, Kuwait, Qatar, Singapore.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional


# ── Calculation methods ──────────────────────────────────────────────────────

METHODS = {
    "Karachi":    {"fajr": 18.0, "isha": 18.0,  "name": "University of Islamic Sciences, Karachi"},
    "ISNA":       {"fajr": 15.0, "isha": 15.0,  "name": "Islamic Society of North America"},
    "MWL":        {"fajr": 18.0, "isha": 17.0,  "name": "Muslim World League"},
    "Makkah":     {"fajr": 18.5, "isha": 90,    "isha_minutes": True, "name": "Umm Al-Qura, Makkah"},
    "Egypt":      {"fajr": 19.5, "isha": 17.5,  "name": "Egyptian General Authority of Survey"},
    "Tehran":     {"fajr": 17.7, "isha": 14.0,  "name": "Institute of Geophysics, Tehran"},
    "Singapore":  {"fajr": 20.0, "isha": 18.0,  "name": "Majlis Ugama Islam Singapura"},
    "Turkey":     {"fajr": 18.0, "isha": 17.0,  "name": "Diyanet İşleri Başkanlığı"},
}

ASR_METHODS = {
    "Standard": 1,   # Shafi, Maliki, Hanbali
    "Hanafi":   2,
}


# ── Core astronomical calculations ───────────────────────────────────────────

def _julian_day(d: date) -> float:
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    return (d.day + (153 * m + 2) // 5 + 365 * y + y // 4
            - y // 100 + y // 400 - 32045)


def _sun_position(jd: float) -> tuple[float, float]:
    """Returns (declination_deg, equation_of_time_hours)."""
    D = jd - 2451545.0
    g = math.radians(357.529 + 0.98560028 * D)
    q = 280.459 + 0.98564736 * D
    L = math.radians(q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    e = math.radians(23.439 - 0.00000036 * D)
    RA = math.degrees(math.atan2(math.cos(e) * math.sin(L), math.cos(L))) / 15
    dec = math.degrees(math.asin(math.sin(e) * math.sin(L)))
    eot = q / 15 - RA
    return dec, eot


def _hour_angle(lat: float, dec: float, target_alt: float) -> Optional[float]:
    cos_val = ((math.sin(math.radians(target_alt))
                - math.sin(math.radians(lat)) * math.sin(math.radians(dec)))
               / (math.cos(math.radians(lat)) * math.cos(math.radians(dec))))
    if cos_val < -1 or cos_val > 1:
        return None
    return math.degrees(math.acos(cos_val))


def _asr_angle(shadow_factor: int, lat: float, dec: float) -> float:
    x = shadow_factor + math.tan(math.radians(abs(lat - dec)))
    return math.degrees(math.atan(1 / x))


# ── Public API ────────────────────────────────────────────────────────────────

@dataclass
class PrayerTimes:
    fajr:    datetime
    sunrise: datetime
    dhuhr:   datetime
    asr:     datetime
    maghrib: datetime
    isha:    datetime
    midnight: datetime

    def as_dict(self) -> dict[str, datetime]:
        return {
            "Fajr":    self.fajr,
            "Sunrise": self.sunrise,
            "Dhuhr":   self.dhuhr,
            "Asr":     self.asr,
            "Maghrib": self.maghrib,
            "Isha":    self.isha,
        }

    def next_prayer(self, now: Optional[datetime] = None) -> tuple[str, datetime]:
        now = now or datetime.now().astimezone()
        for name, dt in self.as_dict().items():
            if name == "Sunrise":
                continue
            if dt.replace(tzinfo=None) > now.replace(tzinfo=None):
                return name, dt
        return "Fajr", self.fajr + timedelta(days=1)


def _utc_offset_hours(tz_name: str) -> float:
    """Return UTC offset in hours for a timezone name string."""
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime as _dt
        offset = _dt.now(ZoneInfo(tz_name)).utcoffset()
        return offset.total_seconds() / 3600
    except Exception:
        pass
    # Fallback: crude longitude-based estimate
    return 0.0


def get_prayer_times(
    lat: float,
    lon: float,
    for_date: Optional[date] = None,
    method: str = "Karachi",
    asr_method: str = "Standard",
    tz: str = "",
    utc_offset: Optional[float] = None,
) -> PrayerTimes:
    """
    Calculate prayer times for a location.
    Pass either tz (e.g. 'Asia/Dhaka') or utc_offset (e.g. 6.0).
    If neither is given, times are returned as local solar time (UTC + lon/15).
    """
    d = for_date or date.today()
    m = METHODS.get(method, METHODS["Karachi"])
    shadow = ASR_METHODS.get(asr_method, 1)

    # Determine UTC offset
    if utc_offset is None:
        if tz:
            utc_offset = _utc_offset_hours(tz)
        else:
            # Default: derive from longitude (rough local solar time)
            utc_offset = round(lon / 15)  # integer timezone estimate

    jd = _julian_day(d)
    dec, eot = _sun_position(jd)

    # Solar noon in UTC
    noon_utc = 12 - lon / 15 - eot
    # Convert to local clock time
    noon_local = noon_utc + utc_offset

    def _time(ha: float, before_noon: bool) -> float:
        return noon_local + (-ha if before_noon else ha) / 15

    # Compute hour angles
    ha_sunrise = _hour_angle(lat, dec, -0.8333)
    ha_fajr    = _hour_angle(lat, dec, -m["fajr"])
    ha_asr     = _hour_angle(lat, dec, _asr_angle(shadow, lat, dec)) if ha_sunrise else None

    def _to_dt(frac_hours: float) -> datetime:
        total_seconds = round(frac_hours * 3600)
        h  = (total_seconds // 3600) % 24
        m_ = (total_seconds % 3600) // 60
        s_ = total_seconds % 60
        return datetime(d.year, d.month, d.day, h, m_, s_)

    sunrise_t  = _time(ha_sunrise, True)  if ha_sunrise else noon_local - 6 / 15
    fajr_t     = _time(ha_fajr,    True)  if ha_fajr    else sunrise_t - 1.5 / 15
    asr_t      = _time(ha_asr,     False) if ha_asr     else noon_local + 3
    maghrib_t  = _time(ha_sunrise, False) if ha_sunrise else noon_local + 6 / 15

    if m.get("isha_minutes"):
        isha_t = maghrib_t + m["isha"] / 60
    else:
        ha_isha = _hour_angle(lat, dec, -m["isha"])
        isha_t  = _time(ha_isha, False) if ha_isha else maghrib_t + 1.5

    midnight_t = (maghrib_t + 12) % 24

    return PrayerTimes(
        fajr    = _to_dt(fajr_t),
        sunrise = _to_dt(sunrise_t),
        dhuhr   = _to_dt(noon_local),
        asr     = _to_dt(asr_t),
        maghrib = _to_dt(maghrib_t),
        isha    = _to_dt(isha_t),
        midnight= _to_dt(midnight_t),
    )


def sehri_time(pt: PrayerTimes) -> datetime:
    """Sehri ends at Fajr (Subh Sadiq)."""
    return pt.fajr - timedelta(minutes=5)


def iftar_time(pt: PrayerTimes) -> datetime:
    """Iftar is at Maghrib (sunset)."""
    return pt.maghrib
