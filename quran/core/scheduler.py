"""
Background scheduler — prayer reminders, reading goals, Ramadan alerts.
Runs as a persistent daemon (systemd/launchd/Task Scheduler).
"""
from __future__ import annotations
import os
import sys
import json
import signal
import logging
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional

PID_FILE = Path.home() / ".local" / "share" / "quran-cli" / "daemon.pid"
LOG_FILE = Path.home() / ".local" / "share" / "quran-cli" / "daemon.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def _schedule_today(cfg: dict) -> None:
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from quran.core.prayer_times import get_prayer_times, sehri_time, iftar_time
        from quran.core.location import detect_location
        from quran.core.notifier import notify_all
        from quran.core.ramadan import is_ramadan

        loc     = detect_location()
        method  = cfg.get("method", "Karachi")
        asr_m   = cfg.get("asr_method", "Standard")
        topic   = cfg.get("remind", {}).get("phone_topic", "")
        pt      = get_prayer_times(loc["lat"], loc["lon"], method=method, asr_method=asr_m,
        tz=loc.get("tz", ""))
        ramadan = is_ramadan()

        scheduler = BlockingScheduler(timezone="UTC")

        def _add(name: str, dt: datetime, title: str, msg: str) -> None:
            if dt > datetime.now():
                scheduler.add_job(
                    notify_all, "date", run_date=dt,
                    args=[title, msg, topic],
                    id=name, replace_existing=True,
                )

        city = loc.get("city", "")
        _add("fajr",    pt.fajr,    "🕌 Fajr",    f"Fajr time in {city}")
        _add("dhuhr",   pt.dhuhr,   "🕌 Dhuhr",   f"Dhuhr time in {city}")
        _add("asr",     pt.asr,     "🕌 Asr",     f"Asr time in {city}")
        _add("maghrib", pt.maghrib, "🕌 Maghrib", f"Maghrib time in {city}")
        _add("isha",    pt.isha,    "🕌 Isha",    f"Isha time in {city}")

        if ramadan:
            sehri_warn = sehri_time(pt) - timedelta(
                minutes=cfg.get("ramadan", {}).get("notify_sehri_min", 15)
            )
            iftar_warn = pt.maghrib - timedelta(
                minutes=cfg.get("ramadan", {}).get("notify_iftar_min", 15)
            )
            _add("sehri_warn", sehri_warn, "☽ Sehri ending",
                 f"Sehri ends in {cfg.get('ramadan',{}).get('notify_sehri_min',15)} min")
            _add("iftar_warn", iftar_warn, "☽ Iftar soon",
                 f"Iftar in {cfg.get('ramadan',{}).get('notify_iftar_min',15)} min — Maghrib at {pt.maghrib.strftime('%I:%M %p')}")
            _add("iftar", pt.maghrib, "☽ Iftar time!",
                 f"Iftar — Alhamdulillah! Break your fast.")

        # Reading goal
        goal_time_str = cfg.get("remind", {}).get("goal_time", "20:00")
        h, m = map(int, goal_time_str.split(":"))
        goal_dt = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        if goal_dt > datetime.now():
            scheduler.add_job(
                notify_all, "date", run_date=goal_dt,
                args=["📖 Reading time", "Time for your daily Quran reading.", topic],
                id="reading_goal", replace_existing=True,
            )

        # Reschedule tomorrow at midnight
        tomorrow_midnight = datetime.now().replace(
            hour=0, minute=5, second=0, microsecond=0
        ) + timedelta(days=1)
        scheduler.add_job(
            lambda: _schedule_today(cfg), "date",
            run_date=tomorrow_midnight, id="reschedule",
        )

        logging.info("Scheduler started. Jobs: %s", scheduler.get_jobs())
        scheduler.start()

    except Exception as e:
        logging.error("Scheduler error: %s", e)


def start_daemon(cfg: dict) -> None:
    """Fork and start scheduler daemon."""
    if os.name == "nt":
        # Windows — run inline (no fork)
        _schedule_today(cfg)
        return

    # Unix — double-fork
    pid = os.fork()
    if pid > 0:
        PID_FILE.write_text(str(pid))
        return  # parent returns

    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        sys.exit(0)

    PID_FILE.write_text(str(os.getpid()))
    _schedule_today(cfg)


def stop_daemon() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        return True
    except (ProcessLookupError, ValueError):
        PID_FILE.unlink(missing_ok=True)
        return False


def daemon_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError, OSError):
        return False
