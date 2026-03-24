"""
Background scheduler — prayer reminders, reading goals, Ramadan alerts.

BUG FIX v1.2.0:
  - Previously used notify_all() which only fired desktop + ntfy.
    Telegram, Gmail, WhatsApp, Webhook were registered as jobs
    but the notification function never reached them.
  - Now uses dispatch_all() from notifier.py which fires ALL channels.
  - Fixed lambda pickling issue (replaced with module-level _fire_job).
  - Added proper daily reschedule at 00:05 to recalculate prayer times.
  - Added Laylatul Qadr special alerts on odd nights of last 10 Ramadan.
"""
from __future__ import annotations
import os
import sys
import logging
import signal
from pathlib import Path
from datetime import date, datetime, timedelta

PID_FILE = Path.home() / ".local" / "share" / "quran-cli" / "daemon.pid"
LOG_FILE = Path.home() / ".local" / "share" / "quran-cli" / "daemon.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ── Module-level job functions (APScheduler pickling safe) ────────────────────
# These must be at module level — not lambdas or nested — for APScheduler.

def _job_prayer(name: str, city: str, topic: str) -> None:
    """Fire a prayer time notification to ALL channels."""
    from quran.core.notifier import dispatch_all
    dispatch_all(
        f"🕌 {name}",
        f"{name} time — {city}",
        topic=topic,
        prayer_name=name,
        notification_type="prayer",
    )
    logging.info("Prayer notification fired: %s", name)


def _job_sehri_warning(minutes: int, city: str, topic: str) -> None:
    """Sehri ending warning."""
    from quran.core.notifier import dispatch_all
    dispatch_all(
        "☽ Sehri ending soon",
        f"Sehri ends in {minutes} minutes — {city}",
        topic=topic,
        notification_type="sehri_warning",
    )
    logging.info("Sehri warning fired (%d min)", minutes)


def _job_iftar_warning(minutes: int, city: str, topic: str, iftar_time_str: str) -> None:
    """Iftar approaching warning."""
    from quran.core.notifier import dispatch_all
    dispatch_all(
        "☽ Iftar approaching",
        f"Iftar in {minutes} minutes ({iftar_time_str}) — {city}",
        topic=topic,
        notification_type="iftar_warning",
    )
    logging.info("Iftar warning fired (%d min)", minutes)


def _job_iftar(city: str, topic: str) -> None:
    """Iftar time — break the fast."""
    from quran.core.notifier import dispatch_all
    dispatch_all(
        "☽ Iftar time — Alhamdulillah!",
        f"Break your fast — {city}. Allahu Akbar!",
        topic=topic,
        notification_type="iftar",
    )
    logging.info("Iftar notification fired")


def _job_reading_goal(goal_ayahs: int, topic: str) -> None:
    """Daily Quran reading reminder."""
    from quran.core.notifier import dispatch_all
    dispatch_all(
        "📖 Quran reading time",
        f"Time for your {goal_ayahs} ayahs — quran read",
        topic=topic,
        notification_type="reading_goal",
    )
    logging.info("Reading goal notification fired")


def _job_laylatul_qadr(night: int, topic: str) -> None:
    """Special Laylatul Qadr alert."""
    from quran.core.notifier import dispatch_all
    dispatch_all(
        f"✨ Laylatul Qadr — Night {night}",
        f"Tonight (night {night}) may be Laylatul Qadr. Increase your worship.",
        topic=topic,
        notification_type="laylatul_qadr",
        priority="high",
    )
    logging.info("Laylatul Qadr notification fired: night %d", night)


def _job_reschedule(cfg_path: str) -> None:
    """Reschedule tomorrow's prayer times at 00:05."""
    import json
    try:
        with open(cfg_path) as f:
            cfg = json.load(f)
    except Exception:
        from quran.config.settings import load
        cfg = load()
    _schedule_today(cfg)
    logging.info("Daily reschedule completed")


# ── Main scheduler setup ──────────────────────────────────────────────────────

def _schedule_today(cfg: dict) -> None:
    """
    Calculate today's prayer times and schedule all notifications.
    Called once at startup and again each day at 00:05.
    """
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from quran.core.prayer_times import get_prayer_times, sehri_time, iftar_time
        from quran.core.location import detect_location
        from quran.core.ramadan import is_ramadan, ramadan_day, LAYLATUL_QADR_NIGHTS

        loc    = detect_location()
        method = cfg.get("method", "Karachi")
        asr_m  = cfg.get("asr_method", "Standard")
        topic  = cfg.get("remind", {}).get("phone_topic", "")
        city   = loc.get("city", "")

        pt     = get_prayer_times(
            loc["lat"], loc["lon"],
            method=method, asr_method=asr_m,
            tz=loc.get("tz", ""),
        )
        ramadan = is_ramadan()
        now     = datetime.now()

        scheduler = BlockingScheduler(timezone="UTC")

        def _add(job_id: str, dt: datetime, fn, fn_args: list) -> None:
            """Add a job only if it's still in the future."""
            if dt > now:
                scheduler.add_job(
                    fn, "date", run_date=dt,
                    args=fn_args,
                    id=job_id, replace_existing=True,
                    misfire_grace_time=300,  # 5 min grace for missed jobs
                )
                logging.info("Scheduled %s at %s", job_id, dt.strftime("%H:%M"))

        # ── 5 daily prayer notifications ─────────────────────────────────────
        advance_m = cfg.get("remind", {}).get("advance_min", 10)
        
        for p_id, p_time, p_name in [
            ("fajr", pt.fajr, "Fajr"),
            ("dhuhr", pt.dhuhr, "Dhuhr"),
            ("asr", pt.asr, "Asr"),
            ("maghrib", pt.maghrib, "Maghrib"),
            ("isha", pt.isha, "Isha")
        ]:
            # 1. Actual prayer time
            _add(p_id, p_time, _job_prayer, [p_name, city, topic])
            
            # 2. Advance reminder (if configured)
            if advance_m > 0:
                _add(f"{p_id}_warn", p_time - timedelta(minutes=advance_m),
                     _job_prayer, [f"{p_name} (in {advance_m}m)", city, topic])

        # ── Fasting & Ramadan notifications ──────────────────────────────────
        remind = cfg.get("remind", {})
        f_sehri = remind.get("fasting_sehri", False)
        f_iftar = remind.get("fasting_iftar", False)

        if ramadan or f_sehri or f_iftar:
            sehri_end = sehri_time(pt)
            iftar     = iftar_time(pt)
            iftar_str = iftar.strftime("%I:%M %p")

            s_min = cfg.get("ramadan", {}).get("notify_sehri_min", 15) if ramadan else remind.get("fasting_sehri_min", 30)
            i_min = cfg.get("ramadan", {}).get("notify_iftar_min", 15) if ramadan else remind.get("fasting_iftar_min", 10)

            if ramadan or f_sehri:
                _add("sehri_warn", sehri_end - timedelta(minutes=s_min),
                     _job_sehri_warning, [s_min, city, topic])

            if ramadan or f_iftar:
                _add("iftar_warn", iftar - timedelta(minutes=i_min),
                     _job_iftar_warning, [i_min, city, topic, iftar_str])
                _add("iftar", iftar,
                     _job_iftar, [city, topic])

            # Laylatul Qadr alert (Isha time on odd nights 21-29)
            if ramadan:
                rd = ramadan_day()
                if rd and rd in LAYLATUL_QADR_NIGHTS:
                    _add("laylatul_qadr", pt.isha,
                         _job_laylatul_qadr, [rd, topic])

        # ── Daily reading goal reminder ───────────────────────────────────────
        goal_time = remind.get("goal_time", "20:00")
        goal_n    = remind.get("goal_ayahs", 5)
        try:
            gh, gm = map(int, goal_time.split(":"))
            goal_dt = now.replace(hour=gh, minute=gm, second=0, microsecond=0)
            _add("reading_goal", goal_dt,
                 _job_reading_goal, [goal_n, topic])
        except ValueError:
            pass

        # ── Daily reschedule at 00:05 the next morning ───────────────────────
        # Uses a module-level function (not a lambda) so APScheduler can
        # serialize it properly.
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=5, second=0, microsecond=0
        )
        import json, tempfile, os as _os
        cfg_tmp = _os.path.join(tempfile.gettempdir(), "quran_cli_cfg.json")
        with open(cfg_tmp, "w") as f:
            json.dump(cfg, f)

        scheduler.add_job(
            _job_reschedule, "date", run_date=tomorrow,
            args=[cfg_tmp],
            id="daily_reschedule", replace_existing=True,
        )

        logging.info(
            "Scheduler started for %s. Jobs: %d",
            city, len(scheduler.get_jobs())
        )
        scheduler.start()

    except Exception as e:
        logging.error("Scheduler error: %s", e)


# ── Daemon management ─────────────────────────────────────────────────────────

def start_daemon(cfg: dict) -> None:
    """Fork and run the scheduler as a background daemon."""
    if os.name == "nt":
        # Windows — no fork available; run inline
        _schedule_today(cfg)
        return

    # Unix — double-fork daemonization
    pid = os.fork()
    if pid > 0:
        # Parent: record child PID and return immediately
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(pid))
        return

    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        sys.exit(0)

    # Grandchild — the actual daemon
    PID_FILE.write_text(str(os.getpid()))

    # Redirect stdio
    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, "r") as fn:
        os.dup2(fn.fileno(), sys.stdin.fileno())
    with open(str(LOG_FILE), "a") as fl:
        os.dup2(fl.fileno(), sys.stdout.fileno())
        os.dup2(fl.fileno(), sys.stderr.fileno())

    _schedule_today(cfg)


def stop_daemon() -> bool:
    """Stop the background scheduler daemon."""
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
    """Check if the scheduler daemon is currently running."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError, OSError):
        PID_FILE.unlink(missing_ok=True)
        return False
