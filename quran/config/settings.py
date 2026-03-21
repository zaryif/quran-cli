"""
Config management — reads/writes ~/.config/quran-cli/config.toml
"""
import sys
import json
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

try:
    import tomllib as _tl
    _has_tomllib = True
except ImportError:
    _has_tomllib = False

CONFIG_DIR  = Path.home() / ".config" / "quran-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DATA_DIR    = Path.home() / ".local" / "share" / "quran-cli"

DEFAULTS = {
    "lang":         "en",
    "method":       "Karachi",        # prayer calculation method
    "asr_method":   "Standard",       # Standard | Hanafi
    "location": {
        "city":    "Dhaka",
        "country": "BD",
        "lat":     23.8103,
        "lon":     90.4125,
        "tz":      "Asia/Dhaka",
        "auto":    True,
    },
    "remind": {
        "enabled":      False,
        "goal_ayahs":   5,
        "goal_time":    "20:00",
        "phone_topic":  "",
        "adhan_sound":  True,
    },
    "display": {
        "arabic":        True,
        "transliteration": False,
        "dual":          False,
        "theme":         "dark",
    },
    "ramadan": {
        "notify_sehri_min": 15,
        "notify_iftar_min": 15,
    }
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save(DEFAULTS)
        return DEFAULTS.copy()
    with open(CONFIG_FILE, "rb") as f:
        user = tomllib.load(f)
    return _deep_merge(DEFAULTS, user)


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = _dict_to_toml(cfg)
    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def _dict_to_toml(d: dict, prefix: str = "") -> list[str]:
    """Minimal TOML serialiser (no external dep)."""
    lines = []
    scalars = {k: v for k, v in d.items() if not isinstance(v, dict)}
    tables  = {k: v for k, v in d.items() if isinstance(v, dict)}
    for k, v in scalars.items():
        if isinstance(v, bool):
            lines.append(f"{k} = {'true' if v else 'false'}")
        elif isinstance(v, str):
            lines.append(f'{k} = "{v}"')
        elif isinstance(v, (int, float)):
            lines.append(f"{k} = {v}")
    for k, v in tables.items():
        section = f"{prefix}.{k}" if prefix else k
        lines.append(f"\n[{section}]")
        lines.extend(_dict_to_toml(v, section))
    return lines


def get(key: str, default=None):
    """Dot-notation getter: get('location.city')"""
    cfg = load()
    parts = key.split(".")
    val = cfg
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return default
    return val if val is not None else default


def set_key(key: str, value) -> None:
    """Dot-notation setter: set_key('display.dual', True)"""
    cfg = load()
    parts = key.split(".")
    d = cfg
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    # coerce type
    try:
        if value.lower() in ("true", "yes"):
            value = True
        elif value.lower() in ("false", "no"):
            value = False
        elif "." in value:
            value = float(value)
        else:
            value = int(value)
    except (AttributeError, ValueError):
        pass
    d[parts[-1]] = value
    save(cfg)
