"""
Notifier — OS-native notifications via plyer + cross-device push via ntfy.sh.
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


def notify_local(title: str, message: str, timeout: int = 8) -> None:
    """Send OS-native notification."""
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


def notify_phone(title: str, message: str, topic: str, priority: str = "default") -> None:
    """Push notification to phone via ntfy.sh."""
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


def notify_all(title: str, message: str, topic: str = "") -> None:
    notify_local(title, message)
    if topic:
        notify_phone(title, message, topic)


def generate_phone_link(topic: str) -> str:
    """Returns ntfy.sh subscription URL + QR-printable string."""
    return f"https://ntfy.sh/{topic}"
