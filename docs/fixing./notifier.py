"""
Notifier — unified notification dispatch for quran-cli.

Hierarchy (all fire in parallel threads):
  1. Desktop  — plyer OS-native popup (always on)
  2. ntfy.sh  — free phone push (if phone_topic configured)
  3. Connectors — Telegram, WhatsApp, Gmail, Webhook (if configured)

BUG FIX v1.2.0:
  Previous notify_all() only called desktop + ntfy.
  Telegram/Gmail/WhatsApp jobs were registered in the scheduler
  but the notification function never dispatched to them.
  dispatch_all() now calls ALL configured channels.
"""
from __future__ import annotations
import threading
from typing import Optional

try:
    from plyer import notification as _plyer_notification
    _PLYER = True
except ImportError:
    _PLYER = False

try:
    import httpx
    _HTTPX = True
except ImportError:
    _HTTPX = False


# ── Low-level senders ─────────────────────────────────────────────────────────

def notify_local(title: str, message: str, timeout: int = 8) -> None:
    """Send OS-native desktop notification via plyer."""
    if not _PLYER:
        print(f"\n[REMINDER] {title}: {message}")
        return
    try:
        _plyer_notification.notify(
            title=title,
            message=message,
            app_name="quran-cli",
            timeout=timeout,
        )
    except Exception:
        print(f"\n[{title}] {message}")


def notify_phone(title: str, message: str, topic: str,
                 priority: str = "default") -> None:
    """Push notification to phone via ntfy.sh (free, no account)."""
    if not _HTTPX or not topic:
        return

    def _send():
        try:
            httpx.post(
                f"https://ntfy.sh/{topic}",
                content=message.encode(),
                headers={
                    "Title": title,
                    "Priority": priority,
                    "Tags": "mosque,crescent_moon",
                },
                timeout=5.0,
            )
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()


# ── Unified dispatcher — THIS is what the scheduler should call ──────────────

def dispatch_all(title: str, message: str, topic: str = "", **kwargs) -> None:
    """
    Send prayer/Ramadan notification to ALL configured channels:
      - Desktop (plyer)          — always
      - ntfy.sh (phone push)     — if phone_topic configured
      - Telegram                 — if quran connect telegram was run
      - WhatsApp (Twilio)        — if quran connect whatsapp was run
      - Gmail                    — if quran connect gmail was run
      - Webhook (Discord/Slack)  — if quran connect webhook was run

    This is the single function the scheduler must call.
    The old notify_all() only called desktop + ntfy — Telegram/Gmail
    were silently skipped. Fixed in v1.2.0.
    """
    # 1. Desktop notification (instant, synchronous)
    notify_local(title, message)

    # 2. ntfy.sh phone push (async thread)
    if topic:
        notify_phone(title, message, topic)

    # 3. All connector channels (Telegram, WhatsApp, Gmail, Webhook)
    #    Each fires in its own thread inside dispatch() already.
    try:
        from quran.connectors import dispatch as _dispatch
        _dispatch(title, message, **kwargs)
    except Exception:
        pass  # connectors not installed / not configured — skip silently


# ── Legacy wrapper (keep for backwards compatibility) ─────────────────────────

def notify_all(title: str, message: str, topic: str = "") -> None:
    """
    Legacy function — now delegates to dispatch_all().
    Kept for any code that imports this directly.
    """
    dispatch_all(title, message, topic=topic)


def generate_phone_link(topic: str) -> str:
    """Returns ntfy.sh subscription URL."""
    return f"https://ntfy.sh/{topic}"
