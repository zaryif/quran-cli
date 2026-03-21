"""
Location detection — auto via ip-api.com, manual override via config.
"""
from __future__ import annotations
import httpx
from rich.console import Console

console = Console()

_CACHE: dict | None = None


def detect_location(force: bool = False) -> dict:
    """
    Returns a dict with: city, country, lat, lon, tz, isp.
    Tries ip-api.com first; falls back to config on failure.
    """
    global _CACHE
    if _CACHE and not force:
        return _CACHE

    from quran.config.settings import load, save
    cfg = load()

    if not cfg["location"].get("auto") and not force:
        _CACHE = cfg["location"]
        return _CACHE

    try:
        r = httpx.get(
            "http://ip-api.com/json/?fields=city,country,countryCode,lat,lon,timezone,isp",
            timeout=4.0,
        )
        data = r.json()
        if data.get("status") == "fail":
            raise ValueError("ip-api returned fail status")
        loc = {
            "city":    data["city"],
            "country": data.get("countryCode", data.get("country", "")),
            "lat":     data["lat"],
            "lon":     data["lon"],
            "tz":      data["timezone"],
            "auto":    True,
        }
        cfg["location"] = loc
        save(cfg)
        _CACHE = loc
        return loc
    except Exception:
        # Fall back to stored config
        _CACHE = cfg["location"]
        return _CACHE


def location_string(loc: dict | None = None) -> str:
    if loc is None:
        loc = detect_location()
    return f"{loc.get('city','?')}, {loc.get('country','?')}"
