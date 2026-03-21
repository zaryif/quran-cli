"""
Quran-CLI AI Guide — RAG system over real Quran text + authentic Hadith.

Data sources (all free, no API key):
  Quran:   AlQuran.cloud API  — https://api.alquran.cloud/v1/
  Hadith:  fawazahmed0/hadith-api on jsDelivr CDN —
           https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/

The hadith-api contains: Sahih Bukhari, Sahih Muslim, Abu Dawud, Tirmidhi,
Nasa'i, Ibn Majah — all authentic collections (Kutub al-Sittah).

NO mock data. Corpus is seeded from real API calls and cached in SQLite.
"""
from __future__ import annotations
import json
import re
import sqlite3
from pathlib import Path
from typing import Optional

try:
    from rank_bm25 import BM25Okapi
    _BM25 = True
except ImportError:
    _BM25 = False

DB_PATH = Path.home() / ".local" / "share" / "quran-cli" / "rag.db"

# Hadith collection identifiers — fawazahmed0/hadith-api (free, CDN)
HADITH_COLLECTIONS = {
    "bukhari": "eng-bukhari",
    "muslim":  "eng-muslim",
    "abudawud":"eng-abudawud",
    "tirmidhi":"eng-tirmidhi",
    "nasai":   "eng-nasai",
    "ibnmajah":"eng-ibnmajah",
}

# Important Hadith references: (collection, book, hadith_number, topic_tags)
# These are referenced by Islamic scholars — all authentic (Sahih/Hasan grade)
HADITH_REFS = [
    ("bukhari", 1,  1, ["intention","niyyah","deeds","sincerity","ikhlas","actions"]),
    ("bukhari", 2, 21, ["prayer","salah","parents","deeds","amal","best"]),
    ("bukhari", 3, 31, ["ramadan","fasting","sawm","forgiveness","faith","reward"]),
    ("bukhari", 6,  2, ["quran","learning","teaching","knowledge","best"]),
    ("bukhari", 8,  2, ["pillars","islam","salah","zakat","hajj","fasting","shahada"]),
    ("bukhari",13,  1, ["friday","jummah","best","day","week"]),
    ("bukhari",54,  1, ["laylatul qadr","ramadan","odd nights","last ten","worship"]),
    ("bukhari",67, 70, ["parents","mother","companionship","kindness","birr"]),
    ("bukhari",73,  1, ["consistency","deeds","amal","worship","beloved","small"]),
    ("bukhari",78,  9, ["smile","charity","sadaqah","brother","kindness"]),
    ("muslim",  4,126, ["prayer","salah","jummah","ramadan","expiation","sin"]),
    ("muslim",  6, 38, ["hardship","patience","trial","expiation","mercy","sabr"]),
    ("muslim", 11,  4, ["charity","help","relief","brotherhood","judgment"]),
    ("muslim", 32, 18, ["brotherhood","love","iman","faith","community","neighbour"]),
    ("muslim", 45,  5, ["dua","supplication","prayer","answered","allah"]),
    ("abudawud",3,  2, ["ramadan","moon","fasting","start","crescent"]),
    ("abudawud",8,  1, ["wudu","ablution","prayer","purification","clean"]),
    ("tirmidhi",4,  1, ["dhikr","subhanallah","paradise","jannah","remembrance","trees"]),
    ("tirmidhi",27, 1, ["tawakkul","reliance","trust","provision","rizq","bird"]),
    ("tirmidhi",40, 1, ["character","akhlaq","good","best","people","kindness"]),
    ("nasai",  10,  1, ["eid","prayer","eid salah","celebration"]),
    ("ibnmajah",1,  1, ["knowledge","ilm","obligation","every","muslim","seek"]),
    ("ibnmajah",33, 1, ["repentance","tawbah","every","sin","forgiveness"]),
]

# Quran ayahs to index for the guide — surah:ayah pairs with topic tags
QURAN_GUIDE_AYAHS = [
    (1, 1, ["mercy","opening","prayer","guidance","bismillah"]),
    (2,152, ["remembrance","dhikr","gratitude","shukr","remember"]),
    (2,155, ["patience","sabr","trial","test","hardship","fear","hunger"]),
    (2,177, ["righteousness","birr","charity","iman","faith","orphan"]),
    (2,183, ["fasting","sawm","ramadan","taqwa","piety","decreed"]),
    (2,185, ["ramadan","quran","revelation","guidance","fasting","criterion"]),
    (2,186, ["dua","supplication","near","respond","believe","answered"]),
    (2,255, ["ayat ul kursi","protection","allah","throne","tawhid","kursi"]),
    (2,256, ["no compulsion","religion","faith","guidance","taghut"]),
    (2,286, ["burden","ease","soul","hardship","bear","patience","test"]),
    (3, 31, ["love","follow","messenger","prophet","obey","ittiba"]),
    (3,103, ["unity","brotherhood","ummah","rope","divided"]),
    (3,159, ["mercy","leadership","forgiveness","consultation","shura"]),
    (3,190, ["reflection","signs","creation","intellect","tafakkur"]),
    (3,200, ["patience","perseverance","sabr","victory","faith"]),
    (4, 36, ["tawhid","parents","charity","worship","neighbours","orphan"]),
    (6,162, ["intention","prayer","salah","devotion","purpose","living"]),
    (9, 51, ["tawakkul","reliance","trust","qadar","decree","believer"]),
    (13, 28, ["peace","dhikr","remembrance","heart","tranquility","rest"]),
    (14,  7, ["gratitude","shukr","increase","blessing","thankful"]),
    (17, 23, ["parents","respect","worship","kindness","birr","honour"]),
    (17, 44, ["tasbih","glorify","praise","creation","every"]),
    (20, 14, ["tawhid","salah","prayer","worship","remembrance"]),
    (22, 37, ["qurbani","sacrifice","taqwa","piety","eid adha","meat"]),
    (23,  1, ["success","believers","mumin","faith","prayer"]),
    (29, 45, ["prayer","salah","quran","recitation","immorality","evil"]),
    (33, 41, ["dhikr","remembrance","believers","worship","much"]),
    (39, 53, ["forgiveness","mercy","tawbah","repentance","hope","despair","sins"]),
    (49, 13, ["equality","taqwa","piety","creation","mankind","race"]),
    (55, 13, ["blessings","gratitude","rahman","mercy","favors","deny"]),
    (65,  3, ["tawakkul","reliance","trust","decree","qadar","sufficient"]),
    (67,  2, ["death","test","trial","deed","amal","life","creation"]),
    (93,  5, ["hope","promise","provision","rizq","blessing","displease"]),
    (94,  5, ["ease","hardship","relief","patience","hope","difficulty"]),
    (97,  1, ["laylatul qadr","night of power","ramadan","quran","revealed"]),
]


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS corpus (
        id TEXT PRIMARY KEY, source TEXT, reference TEXT,
        text TEXT, keywords TEXT
    )""")
    return con


def _fetch_hadith(collection: str, book: int, number: int) -> Optional[str]:
    """
    Fetch a single hadith from fawazahmed0/hadith-api (jsDelivr CDN).
    Source: https://github.com/fawazahmed0/hadith-api
    URL: https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{collection}/{book}/{number}.json
    Returns the hadith text or None on failure.
    """
    import httpx
    edition = HADITH_COLLECTIONS.get(collection)
    if not edition:
        return None
    url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/{book}/{number}.json"
    try:
        r    = httpx.get(url, timeout=10.0, follow_redirects=True)
        data = r.json()
        # The API returns: {"metadata": {...}, "hadiths": [{"number": n, "arab": "...", "text": "..."}]}
        hadiths = data.get("hadiths", [])
        if hadiths:
            text = hadiths[0].get("text", "").strip()
            # Clean up common prefixes
            text = re.sub(r"^it was narrated (that )?|^narrated [^:]+:", "", text, flags=re.I).strip()
            if text:
                return text
    except Exception:
        pass
    return None


def _fetch_quran_ayah(surah: int, ayah: int) -> Optional[str]:
    """Fetch ayah text from AlQuran.cloud (or local SQLite cache)."""
    try:
        from quran.core.quran_engine import fetch_ayah
        result = fetch_ayah(surah, ayah, "en")
        return result["text"] if result else None
    except Exception:
        return None


def seed_corpus(force: bool = False) -> int:
    """
    Seed the RAG corpus with real data from:
    - AlQuran.cloud (Quran ayahs)
    - fawazahmed0/hadith-api (authentic hadith)

    Returns number of documents added.
    """
    con = _get_db()
    count = 0

    # Seed Quran ayahs
    for surah, ayah_n, tags in QURAN_GUIDE_AYAHS:
        doc_id = f"quran:{surah}:{ayah_n}"
        if not force and con.execute(
            "SELECT 1 FROM corpus WHERE id=?", (doc_id,)
        ).fetchone():
            continue

        text = _fetch_quran_ayah(surah, ayah_n)
        if not text:
            continue

        from quran.core.quran_engine import get_surah_meta
        meta = get_surah_meta(surah)
        ref  = f"{meta['name']} {surah}:{ayah_n}" if meta else f"{surah}:{ayah_n}"

        con.execute(
            "INSERT OR REPLACE INTO corpus(id,source,reference,text,keywords) VALUES(?,?,?,?,?)",
            (doc_id, "quran", ref, text, json.dumps(tags))
        )
        con.commit()
        count += 1

    # Seed Hadith
    col_names = {
        "bukhari": "Sahih Bukhari",  "muslim": "Sahih Muslim",
        "abudawud": "Abu Dawud",     "tirmidhi": "Jami at-Tirmidhi",
        "nasai": "Sunan an-Nasa'i",  "ibnmajah": "Sunan Ibn Majah",
    }
    for col, book, num, tags in HADITH_REFS:
        doc_id = f"hadith:{col}:{book}:{num}"
        if not force and con.execute(
            "SELECT 1 FROM corpus WHERE id=?", (doc_id,)
        ).fetchone():
            continue

        text = _fetch_hadith(col, book, num)
        if not text:
            continue

        ref = f"{col_names.get(col, col)} {book}:{num}"
        con.execute(
            "INSERT OR REPLACE INTO corpus(id,source,reference,text,keywords) VALUES(?,?,?,?,?)",
            (doc_id, "hadith", ref, text, json.dumps(tags))
        )
        con.commit()
        count += 1

    return count


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [w for w in text.split() if len(w) > 2]


class RAGEngine:
    """
    Retrieval-Augmented Generation over Quran + authentic Hadith.
    - Retrieval: BM25 (rank-bm25) over real text fetched from APIs
    - Generation: optional Anthropic LLM (set ANTHROPIC_API_KEY)
    - Offline mode: BM25 search only, shows sources without LLM answer
    """

    def __init__(self):
        self._con   = _get_db()
        self._docs: list[dict] = []
        self._bm25  = None
        self._load()

    def _load(self):
        self._docs = []
        for row in self._con.execute(
            "SELECT id,source,reference,text,keywords FROM corpus"
        ).fetchall():
            self._docs.append({
                "id": row[0], "source": row[1],
                "reference": row[2], "text": row[3],
                "keywords": json.loads(row[4] or "[]"),
            })
        if _BM25 and self._docs:
            corpus     = [_tokenize(d["text"]) + d["keywords"] for d in self._docs]
            self._bm25 = BM25Okapi(corpus)

    def corpus_size(self) -> int:
        return len(self._docs)

    def ensure_seeded(self) -> int:
        """Seed from real APIs if corpus is empty."""
        if self.corpus_size() == 0:
            added = seed_corpus()
            self._load()
            return added
        return 0

    def search(self, query: str, k: int = 8,
               source_filter: Optional[str] = None) -> list[dict]:
        """BM25 retrieval. source_filter: 'quran' | 'hadith' | None"""
        if not self._docs:
            self.ensure_seeded()
            if not self._docs:
                return []

        tokens = _tokenize(query)

        if _BM25 and self._bm25:
            scores = self._bm25.get_scores(tokens)
            ranked = sorted(range(len(self._docs)), key=lambda i: scores[i], reverse=True)
        else:
            def _score(d):
                blob = (d["text"] + " " + " ".join(d["keywords"])).lower()
                return sum(1 for t in tokens if t in blob)
            ranked = sorted(range(len(self._docs)), key=lambda i: _score(self._docs[i]), reverse=True)

        results = []
        for i in ranked:
            d = self._docs[i]
            if source_filter and d["source"] != source_filter:
                continue
            results.append(d)
            if len(results) >= k:
                break
        return results

    def answer(self, query: str,
               source_filter: Optional[str] = None,
               use_llm: bool = True) -> dict:
        """Full RAG: retrieve relevant passages then optionally generate answer."""
        self.ensure_seeded()

        k_q = 5 if source_filter != "hadith" else 0
        k_h = 4 if source_filter != "quran"  else 0

        hits = (self.search(query, k=k_q, source_filter="quran")  if k_q else []) + \
               (self.search(query, k=k_h, source_filter="hadith") if k_h else [])

        if not hits:
            return {"answer": "No relevant passages found in corpus.", "sources": [], "offline": True}

        context = "\n\n".join(
            f"{'[QURAN]' if h['source']=='quran' else '[HADITH]'} "
            f"{h['reference']}: {h['text']}"
            for h in hits
        )

        if not use_llm:
            return {"answer": None, "sources": hits, "context": context, "offline": True}

        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return {
                "answer": None, "sources": hits, "context": context, "offline": True,
                "error": "ANTHROPIC_API_KEY not set. Use --offline to see source passages.",
            }

        try:
            import httpx
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key,
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={
                    "model":      "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "thinking":   {"type": "enabled", "budget_tokens": 800},
                    "system": (
                        "You are a knowledgeable Islamic scholar assistant. "
                        "Answer ONLY based on the provided Quran verses and authentic Hadith. "
                        "If the answer is not in the context, say so clearly. "
                        "Do not fabricate hadith. Cite every claim as [Quran X:Y] or [Collection Book:Num]. "
                        "Mark each hadith as (Sahih). Keep answers respectful and grounded."
                    ),
                    "messages": [{"role": "user",
                                  "content": f"Context:\n{context}\n\nQuestion: {query}"}],
                },
                timeout=30.0,
            )
            data = resp.json()
            answer_text = "".join(
                b["text"] for b in data.get("content", []) if b.get("type") == "text"
            )
            return {"answer": answer_text, "sources": hits, "offline": False}
        except Exception as e:
            return {"answer": None, "sources": hits, "context": context,
                    "offline": True, "error": str(e)}

    def add_document(self, id_: str, source: str, reference: str,
                     text: str, keywords: list[str]) -> None:
        self._con.execute(
            "INSERT OR REPLACE INTO corpus(id,source,reference,text,keywords) VALUES(?,?,?,?,?)",
            (id_, source, reference, text, json.dumps(keywords))
        )
        self._con.commit()
        self._load()
