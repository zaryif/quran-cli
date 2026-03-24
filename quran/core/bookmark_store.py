"""
Bookmark manager — save / load named reading positions.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

BOOKMARK_FILE = Path.home() / ".local" / "share" / "quran-cli" / "bookmarks.json"


def _load() -> dict:
    if not BOOKMARK_FILE.exists():
        return {}
    return json.loads(BOOKMARK_FILE.read_text())


def _save(data: dict) -> None:
    BOOKMARK_FILE.parent.mkdir(parents=True, exist_ok=True)
    BOOKMARK_FILE.write_text(json.dumps(data, indent=2))


def save_bookmark(label: str, b_type: str, note: str = "", **kwargs) -> None:
    data = _load()
    entry = {
        "type": b_type,
        "note": note,
        "saved_at": datetime.now().isoformat()
    }
    entry.update(kwargs)
    data[label] = entry
    _save(data)


def get_bookmark(label: str) -> Optional[dict]:
    return _load().get(label)


def list_bookmarks() -> dict:
    return _load()


def delete_bookmark(label: str) -> bool:
    data = _load()
    if label in data:
        del data[label]
        _save(data)
        return True
    return False
