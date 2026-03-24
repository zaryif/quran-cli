"""
quran-cli Telegram Bot — standalone prayer reminder and Quran assistant.

Free Telegram Bot API — no account required beyond a phone number.
One-time setup: get a token from @BotFather in 30 seconds.

This bot runs as a standalone process and sends:
  - Daily prayer times at Fajr
  - Prayer call notifications (adhan time for each prayer)
  - Sehri warning 15 min before Fajr (Ramadan)
  - Iftar alert at Maghrib (Ramadan)
  - Daily ayah at a configured time
  - Laylatul Qadr alerts on odd nights 21–29

Commands the bot responds to:
  /start       — welcome + subscribe to reminders
  /pray        — today's prayer times for your location
  /schedule    — full day schedule
  /ramadan     — Ramadan timings (if Ramadan)
  /ayah        — random ayah
  /hadith      — hadith of the day
  /settings    — change location or calculation method
  /stop        — unsubscribe from reminders

Usage (standalone):
  python -m quran.bot.telegram_bot
  # or:
  quran bot start

Setup:
  1. Message @BotFather on Telegram → /newbot → get token
  2. quran connect telegram
  3. quran bot start
"""
from __future__ import annotations

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Storage ───────────────────────────────────────────────────────────────────

SUBSCRIBERS_FILE = Path.home() / ".local" / "share" / "quran-cli" / "bot_subscribers.json"


def _load_subscribers() -> dict:
    """Load subscriber data from disk."""
    if not SUBSCRIBERS_FILE.exists():
        return {}
    try:
        return json.loads(SUBSCRIBERS_FILE.read_text())
    except Exception:
        return {}


def _save_subscribers(data: dict) -> None:
    SUBSCRIBERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBSCRIBERS_FILE.write_text(json.dumps(data, indent=2))


# ── Prayer time helpers ───────────────────────────────────────────────────────

def _get_prayer_message(chat_id: str) -> str:
    """Build today's prayer times message for a subscriber."""
    subs = _load_subscribers()
    sub  = subs.get(str(chat_id), {})

    lat    = sub.get("lat",     23.8103)
    lon    = sub.get("lon",     90.4125)
    tz     = sub.get("tz",      "Asia/Dhaka")
    city   = sub.get("city",    "Dhaka")
    method = sub.get("method",  "Karachi")

    try:
        from quran.core.prayer_times import get_prayer_times, sehri_time
        from quran.core.ramadan import is_ramadan, ramadan_day

        pt  = get_prayer_times(lat, lon, method=method, tz=tz)
        ram = is_ramadan()
        rd  = ramadan_day() if ram else None

        lines = [
            f"🕌 *Prayer Times — {city}*",
            f"_{datetime.now().strftime('%A, %d %B %Y')}_",
            "",
        ]

        if ram and rd:
            sehri = sehri_time(pt)
            lines += [
                f"☽ *Ramadan Day {rd}*",
                f"Sehri ends: `{sehri.strftime('%I:%M %p')}`",
                "",
            ]

        times = [
            ("Fajr",    pt.fajr),
            ("Sunrise", pt.sunrise),
            ("Dhuhr",   pt.dhuhr),
            ("Asr",     pt.asr),
            ("Maghrib", pt.maghrib),
            ("Isha",    pt.isha),
        ]

        now = datetime.now()
        for name, dt in times:
            marker = " ◀ next" if dt > now and all(
                t <= now for n, t in times if t < dt
            ) else ""
            lines.append(f"{name}: `{dt.strftime('%I:%M %p')}`{marker}")

        if ram:
            lines += [
                "",
                f"☽ Iftar (Maghrib): `{pt.maghrib.strftime('%I:%M %p')}`",
            ]

        lines += ["", f"_Method: {method}_"]
        return "\n".join(lines)

    except Exception as e:
        return f"Could not calculate prayer times: {e}"


def _get_ayah_message() -> str:
    """Get a random ayah formatted for Telegram."""
    try:
        from quran.core.quran_engine import get_random_ayah, get_surah_meta
        ayah = get_random_ayah("en")
        if not ayah or not ayah.get("text"):
            return "📖 Quran — check internet connection for ayah."
        meta = get_surah_meta(ayah["surah"])
        ref  = f"{meta['name']} {ayah['surah']}:{ayah['ayah']}" if meta else f"{ayah['surah']}:{ayah['ayah']}"
        return f"📖 *Ayah of the Day*\n\n_{ayah['text']}_\n\n— _{ref}_"
    except Exception:
        return "📖 *\"Indeed, with hardship comes ease.\"*\n— _Quran 94:5_"


def _get_hadith_message() -> str:
    """Get today's hadith formatted for Telegram."""
    try:
        from quran.commands.hadith import _DAILY, _fetch_hadith, COLLECTION_NAMES
        idx = (datetime.now().day - 1) % len(_DAILY)
        col, book, num = _DAILY[idx]
        h = _fetch_hadith(col, book, num)
        if not h:
            return "📜 *Hadith of the Day* — check internet connection."
        text = h["text"][:400] + ("…" if len(h["text"]) > 400 else "")
        return f"📜 *Hadith of the Day*\n\n_{text}_\n\n— _{h['reference']}_ (Sahih)"
    except Exception:
        return "📜 *\"Actions are judged by intentions.\"*\n— _Sahih Bukhari 1:1_"


# ── Bot handlers ──────────────────────────────────────────────────────────────

async def _run_bot(token: str) -> None:
    """Run the bot using python-telegram-bot v21+."""
    try:
        from telegram import Update
        from telegram.ext import (
            Application, CommandHandler, ContextTypes,
            MessageHandler, filters,
        )
    except ImportError:
        print(
            "[✗] python-telegram-bot not installed.\n"
            "    pip3 install 'quran-cli[connectors]'  (macOS)\n"
            "    pip  install 'quran-cli[connectors]'  (Linux/Windows)"
        )
        return

    async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = str(update.effective_chat.id)
        subs    = _load_subscribers()

        if chat_id not in subs:
            subs[chat_id] = {
                "chat_id":  chat_id,
                "city":     "Dhaka",
                "lat":      23.8103,
                "lon":      90.4125,
                "tz":       "Asia/Dhaka",
                "method":   "Karachi",
                "enabled":  True,
            }
            _save_subscribers(subs)
            msg = (
                "🕌 *Welcome to quran-cli bot!*\n\n"
                "You're now subscribed to prayer reminders.\n\n"
                "Default location: *Dhaka, Bangladesh*\n"
                "To change: /settings\n\n"
                "Commands:\n"
                "/pray — today's prayer times\n"
                "/schedule — full day schedule\n"
                "/ramadan — Ramadan timings\n"
                "/ayah — random ayah\n"
                "/hadith — hadith of the day\n"
                "/stop — unsubscribe"
            )
        else:
            subs[chat_id]["enabled"] = True
            _save_subscribers(subs)
            msg = "🕌 Welcome back! You're subscribed to prayer reminders."

        await update.message.reply_text(msg, parse_mode="Markdown")

    async def stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = str(update.effective_chat.id)
        subs    = _load_subscribers()
        if chat_id in subs:
            subs[chat_id]["enabled"] = False
            _save_subscribers(subs)
        await update.message.reply_text(
            "You've unsubscribed from reminders.\nSend /start to re-subscribe.",
            parse_mode="Markdown"
        )

    async def pray(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = str(update.effective_chat.id)
        await update.message.reply_text(
            _get_prayer_message(chat_id),
            parse_mode="Markdown"
        )

    async def schedule(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = str(update.effective_chat.id)
        # Full schedule including Ramadan rows
        msg = _get_prayer_message(chat_id)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def ramadan(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            from quran.core.ramadan import is_ramadan, ramadan_day, days_until_ramadan
            from quran.core.prayer_times import get_prayer_times, sehri_time

            chat_id = str(update.effective_chat.id)
            subs    = _load_subscribers()
            sub     = subs.get(chat_id, {})

            lat    = sub.get("lat", 23.8103)
            lon    = sub.get("lon", 90.4125)
            tz     = sub.get("tz",  "Asia/Dhaka")
            city   = sub.get("city", "Dhaka")
            method = sub.get("method", "Karachi")

            if not is_ramadan():
                days = days_until_ramadan()
                if days:
                    await update.message.reply_text(
                        f"☽ *Ramadan begins in {days} days.*\n_Keep making du'a._",
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        "☽ Ramadan dates could not be determined for this year.",
                        parse_mode="Markdown"
                    )
                return

            pt    = get_prayer_times(lat, lon, method=method, tz=tz)
            sehri = sehri_time(pt)
            rd    = ramadan_day()
            iftar = pt.maghrib
            dur   = (iftar - sehri).seconds // 3600

            msg = (
                f"☽ *Ramadan Day {rd}*\n"
                f"_{city}_\n\n"
                f"Sehri ends:  `{sehri.strftime('%I:%M %p')}`\n"
                f"Fajr:        `{pt.fajr.strftime('%I:%M %p')}`\n"
                f"Iftar:       `{iftar.strftime('%I:%M %p')}`\n"
                f"Maghrib:     `{pt.maghrib.strftime('%I:%M %p')}`\n"
                f"Isha:        `{pt.isha.strftime('%I:%M %p')}`\n\n"
                f"Fast duration: *{dur}h*"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")

        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def ayah(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(_get_ayah_message(), parse_mode="Markdown")

    async def hadith_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(_get_hadith_message(), parse_mode="Markdown")

    async def settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = str(update.effective_chat.id)
        await update.message.reply_text(
            "⚙️ *Settings*\n\n"
            "To change your location, send:\n"
            "`/setlocation Dhaka` or `/setlocation 23.8103,90.4125`\n\n"
            "To change prayer method:\n"
            "`/setmethod Karachi` (or ISNA, MWL, Makkah, Egypt, Singapore)\n\n"
            "Current settings available at `/pray`.",
            parse_mode="Markdown"
        )

    async def setlocation(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        import httpx
        chat_id = str(update.effective_chat.id)
        args    = " ".join(ctx.args) if ctx.args else ""

        if not args:
            await update.message.reply_text(
                "Usage: `/setlocation Dhaka` or `/setlocation 23.81,90.41`",
                parse_mode="Markdown"
            )
            return

        # Try lat,lon format
        if "," in args:
            try:
                parts  = args.split(",")
                lat, lon = float(parts[0].strip()), float(parts[1].strip())
                subs = _load_subscribers()
                if chat_id not in subs:
                    subs[chat_id] = {}
                subs[chat_id].update({"lat": lat, "lon": lon, "city": f"{lat:.2f},{lon:.2f}"})
                _save_subscribers(subs)
                await update.message.reply_text(
                    f"✅ Location set: `{lat}, {lon}`", parse_mode="Markdown"
                )
                return
            except ValueError:
                pass

        # Try city name via ip-api geocode (free, no key)
        try:
            r = httpx.get(
                f"http://nominatim.openstreetmap.org/search"
                f"?q={args}&format=json&limit=1",
                timeout=5.0,
                headers={"User-Agent": "quran-cli/1.2.7"}
            )
            results = r.json()
            if results:
                lat  = float(results[0]["lat"])
                lon  = float(results[0]["lon"])
                name = results[0].get("display_name", args).split(",")[0]

                subs = _load_subscribers()
                if chat_id not in subs:
                    subs[chat_id] = {}
                import httpx
                try:
                    r_tz = httpx.get(f"https://timeapi.io/api/TimeZone/coordinate?latitude={lat}&longitude={lon}", timeout=5.0)
                    tz_data = r_tz.json()
                    tz = tz_data.get("timeZone")
                except Exception:
                    tz = "UTC"

                subs[chat_id].update({
                    "lat": lat, "lon": lon,
                    "city": name, "tz": tz
                })
                _save_subscribers(subs)
                await update.message.reply_text(
                    f"✅ Location set: *{name}* (`{lat:.4f}, {lon:.4f}`)\n"
                    f"_Use /pray to verify times._",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"Could not find '{args}'. Try: `/setlocation 23.81,90.41`",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def setmethod(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        valid = ["Karachi", "ISNA", "MWL", "Makkah", "Egypt", "Turkey", "Singapore", "Tehran"]
        args  = " ".join(ctx.args) if ctx.args else ""
        chat_id = str(update.effective_chat.id)

        if not args or args not in valid:
            await update.message.reply_text(
                f"Valid methods: {', '.join(valid)}\n\nUsage: `/setmethod Karachi`",
                parse_mode="Markdown"
            )
            return

        subs = _load_subscribers()
        if chat_id not in subs:
            subs[chat_id] = {}
        subs[chat_id]["method"] = args
        _save_subscribers(subs)
        await update.message.reply_text(
            f"✅ Prayer method set: *{args}*", parse_mode="Markdown"
        )

    # ── Schedule daily notifications ──────────────────────────────────────────

    async def _send_prayer_reminders(app_obj) -> None:
        """Send prayer notifications to all subscribers daily."""
        from quran.core.prayer_times import get_prayer_times, sehri_time
        from quran.core.ramadan import is_ramadan, ramadan_day, LAYLATUL_QADR_NIGHTS
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = AsyncIOScheduler()
        subs      = _load_subscribers()
        now       = datetime.now()

        for chat_id, sub in subs.items():
            if not sub.get("enabled", True):
                continue

            lat    = sub.get("lat", 23.8103)
            lon    = sub.get("lon", 90.4125)
            tz     = sub.get("tz",  "")
            method = sub.get("method", "Karachi")
            city   = sub.get("city", "")

            try:
                pt  = get_prayer_times(lat, lon, method=method, tz=tz)
                ram = is_ramadan()

                async def _send(cid: str, msg: str) -> None:
                    try:
                        await app_obj.bot.send_message(cid, msg, parse_mode="Markdown")
                    except Exception:
                        pass

                # 5 prayer notifications
                for name, dt in [
                    ("Fajr",    pt.fajr),
                    ("Dhuhr",   pt.dhuhr),
                    ("Asr",     pt.asr),
                    ("Maghrib", pt.maghrib),
                    ("Isha",    pt.isha),
                ]:
                    async def _job_telegram_prayer(cid: str, n: str, ci: str) -> None:
                        await app_obj.bot.send_message(cid, f"🕌 *{n}* — {ci}", parse_mode="Markdown")

                    if dt > now:
                        scheduler.add_job(
                            _job_telegram_prayer,
                            "date", run_date=dt,
                            args=[chat_id, name, city],
                            id=f"prayer_{chat_id}_{name}",
                            replace_existing=True,
                            misfire_grace_time=300,
                        )

                # Ramadan alerts
                if ram:
                    sehri = sehri_time(pt)
                    rd    = ramadan_day()

                    sehri_warn = sehri - timedelta(minutes=15)
                    async def _job_telegram_sehri_warning(cid: str) -> None:
                        await app_obj.bot.send_message(cid, "☽ *Sehri ending in 15 minutes.* Eat and make intention.", parse_mode="Markdown")

                    if sehri_warn > now:
                        scheduler.add_job(
                            _job_telegram_sehri_warning,
                            "date", run_date=sehri_warn,
                            args=[chat_id],
                            id=f"sehri_{chat_id}", replace_existing=True,
                            misfire_grace_time=300,
                        )

                    async def _job_telegram_iftar(cid: str) -> None:
                        await app_obj.bot.send_message(cid, "☽ *Iftar time — Alhamdulillah!* Break your fast.", parse_mode="Markdown")

                    if pt.maghrib > now:
                        scheduler.add_job(
                            _job_telegram_iftar,
                            "date", run_date=pt.maghrib,
                            args=[chat_id],
                            id=f"iftar_{chat_id}", replace_existing=True,
                            misfire_grace_time=300,
                        )

                    async def _job_telegram_laylatul_qadr(cid: str, r: int) -> None:
                        await app_obj.bot.send_message(cid, f"✨ *Laylatul Qadr — Night {r}*\n_Increase your worship tonight._", parse_mode="Markdown")

                    if rd and rd in LAYLATUL_QADR_NIGHTS and pt.isha > now:
                        scheduler.add_job(
                            _job_telegram_laylatul_qadr,
                            "date", run_date=pt.isha,
                            args=[chat_id, rd],
                            id=f"laylatul_{chat_id}", replace_existing=True,
                        )

            except Exception:
                continue

        # Daily ayah at 7 AM
        morning = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if morning > now:
            async def _job_telegram_ayah(cid: str) -> None:
                await app_obj.bot.send_message(cid, _get_ayah_message(), parse_mode="Markdown")

            for chat_id, sub in subs.items():
                if sub.get("enabled", True):
                    scheduler.add_job(
                        _job_telegram_ayah,
                        "date", run_date=morning,
                        args=[chat_id],
                        id=f"ayah_{chat_id}", replace_existing=True,
                    )

        scheduler.start()
        return scheduler

    # ── Build and run ─────────────────────────────────────────────────────────

    application = (
        Application.builder()
        .token(token)
        .build()
    )

    application.add_handler(CommandHandler("start",        start))
    application.add_handler(CommandHandler("stop",         stop))
    application.add_handler(CommandHandler("pray",         pray))
    application.add_handler(CommandHandler("schedule",     schedule))
    application.add_handler(CommandHandler("ramadan",      ramadan))
    application.add_handler(CommandHandler("ayah",         ayah))
    application.add_handler(CommandHandler("hadith",       hadith_cmd))
    application.add_handler(CommandHandler("settings",     settings))
    application.add_handler(CommandHandler("setlocation",  setlocation))
    application.add_handler(CommandHandler("setmethod",    setmethod))

    async with application:
        scheduler = await _send_prayer_reminders(application)
        await application.start()
        print("[✓] quran-cli Telegram bot running. Press Ctrl+C to stop.")
        await application.updater.start_polling()
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            scheduler.shutdown()
            await application.updater.stop()
            await application.stop()


# ── Entry point ───────────────────────────────────────────────────────────────

def run(token: Optional[str] = None) -> None:
    """Start the Telegram bot. Token from arg or env TELEGRAM_BOT_TOKEN."""
    if not token:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        from quran.connectors.connectors import load_connectors
        cfg   = load_connectors()
        token = cfg.get("telegram", {}).get("token")

    if not token:
        print(
            "[✗] No Telegram bot token found.\n\n"
            "  1. Message @BotFather on Telegram → /newbot\n"
            "  2. Copy the token\n"
            "  3. Run:  quran connect telegram\n"
            "     or:   export TELEGRAM_BOT_TOKEN=<your-token>\n"
        )
        return

    try:
        asyncio.run(_run_bot(token))
    except KeyboardInterrupt:
        print("\n[✓] Bot stopped.")


if __name__ == "__main__":
    run()
