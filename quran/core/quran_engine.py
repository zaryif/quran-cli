"""
Quran engine — fetches from AlQuran.cloud (free, no API key) and caches in SQLite.

Real data sources (all free, open, no API key required):
  Quran text:   https://api.alquran.cloud/v1/surah/{n}/{edition}
  Search:       https://api.alquran.cloud/v1/search/{word}/all/{edition}
  Editions list:https://api.alquran.cloud/v1/edition

NO mock data. Every ayah is fetched live from the API and cached in local SQLite.
First fetch per surah/language hits the API; all subsequent reads are local (offline).
"""
from __future__ import annotations
import sqlite3
import re
from pathlib import Path
from typing import Optional

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _ARABIC_SUPPORT = True
except ImportError:
    _ARABIC_SUPPORT = False

DB_PATH = Path.home() / ".local" / "share" / "quran-cli" / "quran.db"

# AlQuran.cloud edition identifiers — all free, no key
LANG_EDITIONS: dict[str, str] = {
    "en": "en.sahih",       "bn": "bn.bengali",    "ar": "ar.alafasy",
    "ur": "ur.jalandhry",   "tr": "tr.diyanet",    "fr": "fr.hamidullah",
    "id": "id.indonesian",  "ru": "ru.kuliev",     "de": "de.bubenheim",
    "es": "es.cortes",      "zh": "zh.jian",       "nl": "nl.keyzer",
    "ms": "ms.basmeih",
}

SURAH_META = [
    (1,"Al-Fatihah","The Opening",7,"Makkah"),(2,"Al-Baqarah","The Cow",286,"Madinah"),
    (3,"Ali 'Imran","Family of Imran",200,"Madinah"),(4,"An-Nisa","The Women",176,"Madinah"),
    (5,"Al-Ma'idah","The Table Spread",120,"Madinah"),(6,"Al-An'am","The Cattle",165,"Makkah"),
    (7,"Al-A'raf","The Heights",206,"Makkah"),(8,"Al-Anfal","The Spoils of War",75,"Madinah"),
    (9,"At-Tawbah","The Repentance",129,"Madinah"),(10,"Yunus","Jonah",109,"Makkah"),
    (11,"Hud","Hud",123,"Makkah"),(12,"Yusuf","Joseph",111,"Makkah"),
    (13,"Ar-Ra'd","The Thunder",43,"Madinah"),(14,"Ibrahim","Abraham",52,"Makkah"),
    (15,"Al-Hijr","The Rocky Tract",99,"Makkah"),(16,"An-Nahl","The Bee",128,"Makkah"),
    (17,"Al-Isra","The Night Journey",111,"Makkah"),(18,"Al-Kahf","The Cave",110,"Makkah"),
    (19,"Maryam","Mary",98,"Makkah"),(20,"Ta-Ha","Ta-Ha",135,"Makkah"),
    (21,"Al-Anbiya","The Prophets",112,"Makkah"),(22,"Al-Hajj","The Pilgrimage",78,"Madinah"),
    (23,"Al-Mu'minun","The Believers",118,"Makkah"),(24,"An-Nur","The Light",64,"Madinah"),
    (25,"Al-Furqan","The Criterion",77,"Makkah"),(26,"Ash-Shu'ara","The Poets",227,"Makkah"),
    (27,"An-Naml","The Ant",93,"Makkah"),(28,"Al-Qasas","The Stories",88,"Makkah"),
    (29,"Al-Ankabut","The Spider",69,"Makkah"),(30,"Ar-Rum","The Romans",60,"Makkah"),
    (31,"Luqman","Luqman",34,"Makkah"),(32,"As-Sajdah","The Prostration",30,"Makkah"),
    (33,"Al-Ahzab","The Combined Forces",73,"Madinah"),(34,"Saba","Sheba",54,"Makkah"),
    (35,"Fatir","Originator",45,"Makkah"),(36,"Ya-Sin","Ya Sin",83,"Makkah"),
    (37,"As-Saffat","Those Who Set the Ranks",182,"Makkah"),(38,"Sad","The Letter Sad",88,"Makkah"),
    (39,"Az-Zumar","The Troops",75,"Makkah"),(40,"Ghafir","The Forgiver",85,"Makkah"),
    (41,"Fussilat","Explained in Detail",54,"Makkah"),(42,"Ash-Shura","The Consultation",53,"Makkah"),
    (43,"Az-Zukhruf","The Ornaments of Gold",89,"Makkah"),(44,"Ad-Dukhan","The Smoke",59,"Makkah"),
    (45,"Al-Jathiyah","The Crouching",37,"Makkah"),(46,"Al-Ahqaf","The Wind-Curved Sandhills",35,"Makkah"),
    (47,"Muhammad","Muhammad",38,"Madinah"),(48,"Al-Fath","The Victory",29,"Madinah"),
    (49,"Al-Hujurat","The Rooms",18,"Madinah"),(50,"Qaf","The Letter Qaf",45,"Makkah"),
    (51,"Adh-Dhariyat","The Winnowing Winds",60,"Makkah"),(52,"At-Tur","The Mount",49,"Makkah"),
    (53,"An-Najm","The Star",62,"Makkah"),(54,"Al-Qamar","The Moon",55,"Makkah"),
    (55,"Ar-Rahman","The Beneficent",78,"Madinah"),(56,"Al-Waqi'ah","The Inevitable",96,"Makkah"),
    (57,"Al-Hadid","The Iron",29,"Madinah"),(58,"Al-Mujadila","The Pleading Woman",22,"Madinah"),
    (59,"Al-Hashr","The Exile",24,"Madinah"),(60,"Al-Mumtahanah","She that is to be examined",13,"Madinah"),
    (61,"As-Saf","The Ranks",14,"Madinah"),(62,"Al-Jumu'ah","Friday",11,"Madinah"),
    (63,"Al-Munafiqun","The Hypocrites",11,"Madinah"),(64,"At-Taghabun","The Mutual Disillusion",18,"Madinah"),
    (65,"At-Talaq","The Divorce",12,"Madinah"),(66,"At-Tahrim","The Prohibition",12,"Madinah"),
    (67,"Al-Mulk","The Sovereignty",30,"Makkah"),(68,"Al-Qalam","The Pen",52,"Makkah"),
    (69,"Al-Haqqah","The Reality",52,"Makkah"),(70,"Al-Ma'arij","The Ascending Stairways",44,"Makkah"),
    (71,"Nuh","Noah",28,"Makkah"),(72,"Al-Jinn","The Jinn",28,"Makkah"),
    (73,"Al-Muzzammil","The Enshrouded One",20,"Makkah"),(74,"Al-Muddaththir","The Cloaked One",56,"Makkah"),
    (75,"Al-Qiyamah","The Resurrection",40,"Makkah"),(76,"Al-Insan","The Human",31,"Madinah"),
    (77,"Al-Mursalat","The Emissaries",50,"Makkah"),(78,"An-Naba","The Tidings",40,"Makkah"),
    (79,"An-Nazi'at","Those who drag forth",46,"Makkah"),(80,"Abasa","He Frowned",42,"Makkah"),
    (81,"At-Takwir","The Overthrowing",29,"Makkah"),(82,"Al-Infitar","The Cleaving",19,"Makkah"),
    (83,"Al-Mutaffifin","The Defrauding",36,"Makkah"),(84,"Al-Inshiqaq","The Sundering",25,"Makkah"),
    (85,"Al-Buruj","The Mansions of the Stars",22,"Makkah"),(86,"At-Tariq","The Morning Star",17,"Makkah"),
    (87,"Al-A'la","The Most High",19,"Makkah"),(88,"Al-Ghashiyah","The Overwhelming",26,"Makkah"),
    (89,"Al-Fajr","The Dawn",30,"Makkah"),(90,"Al-Balad","The City",20,"Makkah"),
    (91,"Ash-Shams","The Sun",15,"Makkah"),(92,"Al-Layl","The Night",21,"Makkah"),
    (93,"Ad-Duhaa","The Morning Hours",11,"Makkah"),(94,"Ash-Sharh","The Relief",8,"Makkah"),
    (95,"At-Tin","The Fig",8,"Makkah"),(96,"Al-Alaq","The Clot",19,"Makkah"),
    (97,"Al-Qadr","The Power",5,"Makkah"),(98,"Al-Bayyinah","The Clear Proof",8,"Madinah"),
    (99,"Az-Zalzalah","The Earthquake",8,"Madinah"),(100,"Al-Adiyat","The Courser",11,"Makkah"),
    (101,"Al-Qari'ah","The Calamity",11,"Makkah"),(102,"At-Takathur","The Rivalry in World Increase",8,"Makkah"),
    (103,"Al-Asr","The Declining Day",3,"Makkah"),(104,"Al-Humazah","The Traducer",9,"Makkah"),
    (105,"Al-Fil","The Elephant",5,"Makkah"),(106,"Quraysh","Quraysh",4,"Makkah"),
    (107,"Al-Ma'un","The Small Kindnesses",7,"Makkah"),(108,"Al-Kawthar","The Abundance",3,"Makkah"),
    (109,"Al-Kafirun","The Disbelievers",6,"Makkah"),(110,"An-Nasr","The Divine Support",3,"Madinah"),
    (111,"Al-Masad","The Palm Fiber",5,"Makkah"),(112,"Al-Ikhlas","The Sincerity",4,"Makkah"),
    (113,"Al-Falaq","The Daybreak",5,"Makkah"),(114,"An-Nas","The Mankind",6,"Makkah"),
]

_SURAH_LOOKUP: dict[str, int] = {}
for _r in SURAH_META:
    _SURAH_LOOKUP[_r[1].lower()] = _r[0]
    _SURAH_LOOKUP[_r[2].lower()] = _r[0]
    _clean = re.sub(r"^(al|an|as|az|at|ad)-?'?\s*", "", _r[1].lower()).strip()
    if _clean:
        _SURAH_LOOKUP[_clean] = _r[0]


def resolve_surah(query: str) -> Optional[int]:
    """Resolve surah name or number string to integer 1-114."""
    q = query.strip()
    if q.isdigit():
        n = int(q)
        return n if 1 <= n <= 114 else None
    ql = q.lower().replace("_", " ").strip()
    if ql in _SURAH_LOOKUP:
        return _SURAH_LOOKUP[ql]
    for key, num in _SURAH_LOOKUP.items():
        if ql in key or key in ql:
            return num
    return None


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS ayahs (
        surah INTEGER, ayah INTEGER, lang TEXT,
        text TEXT, transliteration TEXT,
        PRIMARY KEY (surah, ayah, lang))""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_lang ON ayahs(lang)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_sl ON ayahs(surah,lang)")
    con.commit()
    return con


def _fetch_surah_api(surah: int, edition: str) -> list[dict]:
    """Fetch from AlQuran.cloud. Returns empty list on failure."""
    import httpx
    url = f"https://api.alquran.cloud/v1/surah/{surah}/{edition}"
    try:
        r = httpx.get(url, timeout=15.0, follow_redirects=True)
        data = r.json()
        if data.get("code") == 200 and data.get("status") == "OK":
            return data["data"]["ayahs"]
    except Exception:
        pass
    return []


def _cache_surah(surah: int, lang: str) -> bool:
    con = _get_db()
    if con.execute(
        "SELECT COUNT(*) FROM ayahs WHERE surah=? AND lang=?", (surah, lang)
    ).fetchone()[0] > 0:
        return True
    edition = LANG_EDITIONS.get(lang, "en.sahih")
    ayahs   = _fetch_surah_api(surah, edition)
    if not ayahs:
        return False
    con.executemany(
        "INSERT OR REPLACE INTO ayahs(surah,ayah,lang,text,transliteration) VALUES(?,?,?,?,?)",
        [(surah, a["numberInSurah"], lang, a["text"], "") for a in ayahs]
    )
    con.commit()
    return True


def format_arabic(text: str) -> str:
    if not _ARABIC_SUPPORT:
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def get_surah_meta(surah: int) -> Optional[dict]:
    for r in SURAH_META:
        if r[0] == surah:
            return {"number": r[0], "name": r[1], "meaning": r[2],
                    "ayahs": r[3], "type": r[4]}
    return None


def fetch_ayah(surah: int, ayah: int, lang: str = "en") -> Optional[dict]:
    con = _get_db()
    _cache_surah(surah, lang)
    row = con.execute(
        "SELECT text FROM ayahs WHERE surah=? AND ayah=? AND lang=?",
        (surah, ayah, lang)
    ).fetchone()
    if not row:
        return None
    meta = get_surah_meta(surah)
    return {"surah": surah, "ayah": ayah, "text": row[0],
            "ref": f"{meta['name']} {surah}:{ayah}" if meta else f"{surah}:{ayah}",
            "meta": meta}


def fetch_ayah_with_arabic(surah: int, ayah: int, lang: str = "en") -> dict:
    """Fetch ayah with Arabic original + chosen language translation."""
    result = {"surah": surah, "ayah": ayah, "arabic": None, "text": None,
              "meta": get_surah_meta(surah)}
    con = _get_db()
    _cache_surah(surah, "ar")
    ar = con.execute(
        "SELECT text FROM ayahs WHERE surah=? AND ayah=? AND lang='ar'",
        (surah, ayah)
    ).fetchone()
    if ar:
        result["arabic"] = ar[0]
    if lang == "ar":
        result["text"] = result["arabic"]
    else:
        _cache_surah(surah, lang)
        tr = con.execute(
            "SELECT text FROM ayahs WHERE surah=? AND ayah=? AND lang=?",
            (surah, ayah, lang)
        ).fetchone()
        if tr:
            result["text"] = tr[0]
    return result


def fetch_surah(surah: int, lang: str = "en",
                ayah_from: int = 1, ayah_to: Optional[int] = None) -> list[dict]:
    meta = get_surah_meta(surah)
    if not meta:
        return []
    to  = ayah_to or meta["ayahs"]
    con = _get_db()
    if not _cache_surah(surah, lang):
        return []
    rows = con.execute(
        "SELECT ayah,text FROM ayahs WHERE surah=? AND lang=? "
        "AND ayah BETWEEN ? AND ? ORDER BY ayah",
        (surah, lang, ayah_from, to)
    ).fetchall()
    return [{"surah": surah, "ayah": r[0], "text": r[1], "meta": meta} for r in rows]


def fetch_surah_dual(surah: int, lang: str = "en",
                     ayah_from: int = 1, ayah_to: Optional[int] = None) -> list[dict]:
    """Fetch surah with Arabic original + chosen translation side by side."""
    meta = get_surah_meta(surah)
    if not meta:
        return []
    to  = ayah_to or meta["ayahs"]
    con = _get_db()
    _cache_surah(surah, "ar")
    if lang != "ar":
        _cache_surah(surah, lang)

    ar_map = {r[0]: r[1] for r in con.execute(
        "SELECT ayah,text FROM ayahs WHERE surah=? AND lang='ar' "
        "AND ayah BETWEEN ? AND ? ORDER BY ayah", (surah, ayah_from, to)
    ).fetchall()}

    if lang == "ar":
        return [{"surah": surah, "ayah": k, "arabic": v, "text": v, "meta": meta}
                for k, v in sorted(ar_map.items())]

    tr_map = {r[0]: r[1] for r in con.execute(
        "SELECT ayah,text FROM ayahs WHERE surah=? AND lang=? "
        "AND ayah BETWEEN ? AND ? ORDER BY ayah", (surah, lang, ayah_from, to)
    ).fetchall()}

    return [
        {"surah": surah, "ayah": n, "arabic": ar_map.get(n, ""),
         "text": tr_map.get(n, ""), "meta": meta}
        for n in sorted(ar_map.keys())
    ]


def search_quran(query: str, lang: str = "en", limit: int = 20) -> list[dict]:
    """
    Search the Quran.
    Tries AlQuran.cloud search API first, falls back to local SQLite cache.
    API: https://api.alquran.cloud/v1/search/{keyword}/all/{edition}
    """
    edition = LANG_EDITIONS.get(lang, "en.sahih")
    results: list[dict] = []

    try:
        import httpx
        url  = f"https://api.alquran.cloud/v1/search/{query}/all/{edition}"
        r    = httpx.get(url, timeout=12.0, follow_redirects=True)
        data = r.json()
        if data.get("code") == 200:
            con = _get_db()
            for m in data.get("data", {}).get("matches", [])[:limit]:
                sn, an, txt = m["surah"]["number"], m["numberInSurah"], m["text"]
                meta = get_surah_meta(sn) or {
                    "name": m["surah"]["englishName"],
                    "meaning": m["surah"]["englishNameTranslation"],
                    "ayahs": m["surah"]["numberOfAyahs"],
                    "type": m["surah"]["revelationType"], "number": sn,
                }
                con.execute(
                    "INSERT OR REPLACE INTO ayahs(surah,ayah,lang,text,transliteration)"
                    " VALUES(?,?,?,?,?)", (sn, an, lang, txt, "")
                )
                con.commit()
                results.append({"surah": sn, "ayah": an, "text": txt, "meta": meta})
    except Exception:
        pass

    if not results:
        con = _get_db()
        for row in con.execute(
            "SELECT surah,ayah,text FROM ayahs WHERE lang=? AND text LIKE ? LIMIT ?",
            (lang, f"%{query}%", limit)
        ).fetchall():
            results.append({"surah": row[0], "ayah": row[1], "text": row[2],
                            "meta": get_surah_meta(row[0])})
    return results


def get_random_ayah(lang: str = "en") -> dict:
    """
    Returns a random significant ayah.
    All text fetched live from AlQuran.cloud.
    """
    import random
    SIGNIFICANT = [
        (1,1),(2,255),(2,286),(2,152),(13,28),(94,5),(93,5),(65,3),(39,53),(2,177),
        (3,200),(17,23),(29,45),(33,41),(67,2),(20,14),(49,13),(55,13),(9,51),(14,7),
        (22,37),(23,1),(6,162),(3,159),(4,36),(2,183),(2,185),(97,1),(2,187),(3,103),
    ]
    s, a = random.choice(SIGNIFICANT)
    return fetch_ayah_with_arabic(s, a, lang)


def list_surahs() -> list[tuple]:
    return [(r[0], r[1], r[2], r[3], r[4]) for r in SURAH_META]


def cache_status() -> dict:
    """Return stats about the local SQLite cache."""
    result: dict = {"languages": {}, "total_ayahs": 0, "size_mb": 0.0}

    if not DB_PATH.exists():
        return result

    result["size_mb"] = DB_PATH.stat().st_size / (1024 * 1024)

    try:
        con = _get_db()
        # Count distinct surahs per language
        for row in con.execute(
            "SELECT lang, COUNT(DISTINCT surah) FROM ayahs GROUP BY lang"
        ).fetchall():
            result["languages"][row[0]] = row[1]

        total = con.execute("SELECT COUNT(*) FROM ayahs").fetchone()
        result["total_ayahs"] = total[0] if total else 0
    except Exception:
        pass

    return result
