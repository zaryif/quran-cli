"""
quran-cli terminal renderer.

Splash screen shows:
  Arabic text  →  بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ
  English      →  In the name of Allah, the Most Gracious, the Most Merciful
  Lang2        →  আল্লাহর নামে, পরম দয়ালু, অতি মেহেরবান  (or any configured language)

Customise with:
  quran config set lang bn          — primary translation
  quran config set lang2 ur         — secondary translation (shown on splash)
  quran config set display.arabic true/false
  quran config set display.show_en true/false
  quran config set display.show_lang2 true/false
  quran lang                        — interactive language picker
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich import box

console = Console()

# ── Pre-composed Unicode Arabic strings ───────────────────────────────────────
# All correct Unicode — display properly in any modern terminal.
BASMALLAH    = "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ"
AL_QURAN_AR  = "ٱلۡقُرۡءَانُ ٱلۡكَرِيمُ"

# Translations of the Basmallah
BASMALLAH_TRANSLATIONS = {
    "en": "In the name of Allah, the Most Gracious, the Most Merciful",
    "bn": "আল্লাহর নামে, যিনি পরম দয়ালু, অতি মেহেরবান",
    "ur": "اللہ کے نام سے جو بڑا مہربان، نہایت رحم والا ہے",
    "ar": "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ",
    "tr": "Rahman ve Rahim olan Allah'ın adıyla",
    "fr": "Au nom d'Allah, le Tout Miséricordieux, le Très Miséricordieux",
    "id": "Dengan nama Allah Yang Maha Pengasih, Maha Penyayang",
    "ru": "Во имя Аллаха, Милостивого, Милосердного",
    "de": "Im Namen Allahs, des Allerbarmers, des Barmherzigen",
    "es": "En el nombre de Allah, el Compasivo, el Misericordioso",
    "zh": "奉至仁至慈的真主之名",
    "nl": "In de naam van Allah, de Erbarmer, de Genadevolle",
    "ms": "Dengan nama Allah Yang Maha Pemurah lagi Maha Penyayang",
}

LANG_NAMES = {
    "en": "English",  "bn": "বাংলা (Bangla)", "ar": "العربية (Arabic)",
    "ur": "اردو (Urdu)",   "tr": "Türkçe (Turkish)", "fr": "Français (French)",
    "id": "Bahasa Indonesia", "ru": "Русский (Russian)", "de": "Deutsch (German)",
    "es": "Español (Spanish)", "zh": "中文 (Chinese)", "nl": "Nederlands (Dutch)",
    "ms": "Bahasa Melayu",
}


def _shape(text: str) -> str:
    """Properly shape Arabic text for terminal (RTL + ligature joining)."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text


def print_banner() -> None:
    """
    Professional quran-cli splash screen.

    Displays:
      1. Arabic Basmallah (correctly shaped, bold yellow)
      2. English translation
      3. Secondary language translation (default: Bangla)
      4. App name + version
      5. Quick-start command hints
    """
    from quran.config.settings import load
    from quran.core.ramadan import is_ramadan

    cfg  = load()
    ram  = is_ramadan()
    lang = cfg.get("lang", "en")
    lang2 = cfg.get("lang2", "bn")
    show_en    = cfg.get("display", {}).get("show_en", True)
    show_lang2 = cfg.get("display", {}).get("show_lang2", True)
    show_ar    = cfg.get("display", {}).get("arabic", True)

    c = console
    c.print()

    # ── 1. Arabic Basmallah ────────────────────────────────────────────────────
    if show_ar:
        ar_shaped = _shape(BASMALLAH)
        c.print(Align.center(
            Text(ar_shaped, style="bold yellow", justify="center")
        ))
        c.print()

    # ── 2. English translation ─────────────────────────────────────────────────
    if show_en:
        en_text = BASMALLAH_TRANSLATIONS["en"]
        c.print(Align.center(
            Text(en_text, style="white", justify="center")
        ))

    # ── 3. Secondary language translation (Bangla by default) ─────────────────
    if show_lang2 and lang2 and lang2 != "en":
        lang2_text = BASMALLAH_TRANSLATIONS.get(lang2, "")
        if lang2_text and lang2_text != BASMALLAH_TRANSLATIONS.get("en", ""):
            if lang2 == "ar":
                lang2_text = _shape(lang2_text)
            c.print(Align.center(
                Text(lang2_text, style="dim cyan", justify="center")
            ))

    # ── 4. App name ────────────────────────────────────────────────────────────
    c.print()
    c.print(Align.center(Text("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style="bright_black")))
    c.print()
    c.print(Align.center(Text("quran-cli", style="bold green")))
    c.print(Align.center(Text("v1.0.0  ·  Islamic terminal companion", style="dim")))

    if ram:
        c.print()
        c.print(Align.center(Text("☽  Ramadan Mubarak — رَمَضَان مُبَارَك", style="bold yellow")))

    # ── 5. Language note ───────────────────────────────────────────────────────
    primary_name   = LANG_NAMES.get(lang, lang)
    secondary_name = LANG_NAMES.get(lang2, lang2) if lang2 else "—"
    c.print()
    c.print(Align.center(
        Text(
            f"Primary: {primary_name}  ·  Secondary: {secondary_name}  "
            f"·  quran lang — change",
            style="dim"
        )
    ))
    c.print()

    # ── 6. Quick-start panel ───────────────────────────────────────────────────
    commands = [
        ("quran schedule",           "full day — prayers, sehri, iftar"),
        ("quran read 1",             "read Al-Fatihah"),
        ("quran read kahf",          "search surah by name"),
        ("quran read 2:255 --dual",  "Ayat ul-Kursi with Arabic"),
        ("quran pray",               "today's prayer times"),
        ("quran ramadan",            "sehri, iftar & tarawih"),
        ("quran lang",               "change display language"),
        ("quran guide \"...\"",      "Quran & Hadith AI guide"),
        ("quran --help",             "all commands"),
    ]

    rows = "\n".join(
        f"  [green]{cmd:<38}[/green][dim]{desc}[/dim]"
        for cmd, desc in commands
    )

    c.print(Panel(
        rows,
        title="[dim]quick start[/dim]",
        border_style="bright_black",
        padding=(0, 1),
    ))
    c.print()


def print_location_header(loc: dict, is_ramadan: bool = False) -> None:
    city    = loc.get("city", "?")
    country = loc.get("country", "?")
    lat     = loc.get("lat", 0)
    lon     = loc.get("lon", 0)
    auto    = loc.get("auto", False)
    tag = "[green][auto][/green]" if auto else "[dim][manual][/dim]"
    ram = "  [yellow]☽ Ramadan[/yellow]" if is_ramadan else ""
    console.print(
        f" [green]◉[/green]  [bold]{city}, {country}[/bold]  {tag}  "
        f"[dim]{lat:.4f}°N · {lon:.4f}°E[/dim]{ram}"
    )
    console.print()


def print_ayah_arabic(text: str) -> None:
    shaped = _shape(text)
    console.print(Align.right(
        Text(shaped, style="bold yellow", justify="right"),
        width=min(console.width - 4, 80)
    ))


def render_prayer_table(
    times: dict,
    next_name: Optional[str] = None,
    extras: Optional[dict] = None,
) -> None:
    table = Table(
        box=box.SIMPLE, show_header=False,
        padding=(0, 2), border_style="bright_black",
    )
    table.add_column("Prayer", style="dim",   width=12)
    table.add_column("Time",   style="white", width=12)
    table.add_column("",                      width=16)

    ARABIC_NAMES = {
        "Fajr": "فَجْر",     "Sunrise": "شُرُوق",
        "Dhuhr": "ظُهْر",    "Asr": "عَصْر",
        "Maghrib": "مَغْرِب", "Isha": "عِشَاء",
        "Sehri": "سُحُور",   "Iftar": "إِفْطَار",
        "Tarawih": "تَرَاوِيح",
    }

    order = []
    if extras and "Sehri" in extras:
        order.append(("Sehri", True))
    order += [("Fajr", False), ("Sunrise", False), ("Dhuhr", False), ("Asr", False)]
    if extras and "Iftar" in extras:
        order.append(("Iftar", True))
    order += [("Maghrib", False), ("Isha", False)]
    if extras and "Tarawih" in extras:
        order.append(("Tarawih", True))

    all_times = dict(times)
    if extras:
        all_times.update(extras)

    import datetime as _dt
    for name, is_special in order:
        dt = all_times.get(name)
        if not isinstance(dt, _dt.datetime):
            continue
        time_str = dt.strftime("%I:%M %p")
        ar       = _shape(ARABIC_NAMES.get(name, ""))
        is_next  = name == next_name

        if is_next:
            table.add_row(
                f"[bold green]{name}[/bold green]",
                f"[bold green]{time_str}[/bold green]",
                f"[green]▶ next[/green]  [dim]{ar}[/dim]",
            )
        elif is_special:
            table.add_row(
                f"[yellow]{name}[/yellow]",
                f"[yellow]{time_str}[/yellow]",
                f"[dim yellow]{ar}[/dim yellow]",
            )
        elif name == "Sunrise":
            table.add_row(f"[dim]{name}[/dim]", f"[dim]{time_str}[/dim]", f"[dim]{ar}[/dim]")
        else:
            table.add_row(name, time_str, f"[dim]{ar}[/dim]")

    console.print(table)


def render_surah_header(meta: dict) -> None:
    console.print()
    console.print(Rule(
        f"[bold green]{meta['name']}[/bold green]  "
        f"[dim]{meta['meaning']}  ·  {meta['ayahs']} ayahs  ·  {meta['type']}[/dim]",
        style="green"
    ))
    console.print()


def render_schedule_table(rows: list[dict]) -> None:
    table = Table(
        box=box.SIMPLE_HEAD, show_header=True,
        header_style="dim", border_style="bright_black",
        padding=(0, 1),
    )
    table.add_column("Prayer",   width=10)
    table.add_column("Time",     width=12, style="white")
    table.add_column("Progress", width=22)
    table.add_column("Status",   width=10)

    now = datetime.now()

    for row in rows:
        dt      = row["dt"]
        name    = row["name"]
        status  = row.get("status", "open")
        special = row.get("special", False)
        pct     = row.get("pct", 0)

        bar_w  = 18
        filled = int(bar_w * pct / 100)
        empty  = bar_w - filled

        if status == "next":
            bar    = f"[green]{'█' * filled}{'░' * empty}[/green]"
            name_s = f"[bold green]{name}[/bold green]"
            time_s = f"[bold green]{dt.strftime('%I:%M %p')}[/bold green]"
            stat_s = "[green]▶ next[/green]"
        elif status == "done":
            bar    = f"[bright_black]{'█' * filled}{'░' * empty}[/bright_black]"
            name_s = f"[dim]{name}[/dim]"
            time_s = f"[dim]{dt.strftime('%I:%M %p')}[/dim]"
            stat_s = "[dim]✓[/dim]"
        elif special:
            bar    = f"[yellow]{'█' * filled}{'░' * empty}[/yellow]"
            name_s = f"[yellow]{name}[/yellow]"
            time_s = f"[yellow]{dt.strftime('%I:%M %p')}[/yellow]"
            stat_s = "[dim yellow]—[/dim yellow]"
        else:
            bar    = f"[bright_black]{'░' * bar_w}[/bright_black]"
            name_s = name
            time_s = dt.strftime("%I:%M %p")
            stat_s = "[dim]—[/dim]"

        table.add_row(name_s, time_s, bar, stat_s)

    console.print(table)


def countdown_str(dt: datetime) -> str:
    delta = dt - datetime.now()
    total = int(delta.total_seconds())
    if total <= 0:
        return "now"
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"
