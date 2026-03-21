"""
Connector implementations for all notification channels.
"""
from __future__ import annotations
import json
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
from quran.connectors.base import BaseConnector

CONNECTORS_FILE = Path.home() / ".config" / "quran-cli" / "connectors.json"


def load_connectors() -> dict:
    if not CONNECTORS_FILE.exists():
        return {}
    try:
        return json.loads(CONNECTORS_FILE.read_text())
    except Exception:
        return {}


def save_connectors(data: dict) -> None:
    CONNECTORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONNECTORS_FILE.write_text(json.dumps(data, indent=2))
    CONNECTORS_FILE.chmod(0o600)


# ── Desktop (plyer) ────────────────────────────────────────────────────────────

class DesktopConnector(BaseConnector):
    name = "desktop"

    def send(self, title: str, body: str, **kwargs) -> bool:
        import sys
        import subprocess

        # Mac Native Notification via AppleScript
        if sys.platform == "darwin":
            try:
                # Escape quotes for AppleScript
                safe_title = title.replace('"', '\\"')
                safe_body = body.replace('"', '\\"')
                script = f'display notification "{safe_body}" with title "{safe_title}"'
                subprocess.run(["osascript", "-e", script], check=True)
                return True
            except Exception:
                pass

        # Fallback to plyer (Windows/Linux)
        try:
            from plyer import notification
            notification.notify(title=title, message=body,
                                app_name="quran-cli", timeout=8)
            return True
        except Exception:
            print(f"\n[{title}] {body}")
            return True

    def test(self) -> bool:
        return self.send("quran-cli test", "Desktop notifications are working!")

    def setup(self) -> dict:
        return {"enabled": True}

    def is_configured(self, cfg: dict) -> bool:
        return True  # always available


# ── ntfy.sh ────────────────────────────────────────────────────────────────────

class NtfyConnector(BaseConnector):
    name = "ntfy"

    def send(self, title: str, body: str, topic: str = "", **kwargs) -> bool:
        if not topic:
            return False
        try:
            import httpx
            httpx.post(
                f"https://ntfy.sh/{topic}",
                content=body.encode(),
                headers={"Title": title, "Tags": "mosque"},
                timeout=5.0,
            )
            return True
        except Exception:
            return False

    def test(self) -> bool:
        cfg = load_connectors().get("ntfy", {})
        return self.send("quran-cli test", "ntfy.sh is connected!", topic=cfg.get("topic",""))

    def setup(self) -> dict:
        import secrets
        topic = f"quran-{secrets.token_hex(6)}"
        print(f"Subscribe to: https://ntfy.sh/{topic}")
        return {"enabled": True, "topic": topic}

    def is_configured(self, cfg: dict) -> bool:
        return bool(cfg.get("topic"))


# ── Telegram ──────────────────────────────────────────────────────────────────

class TelegramConnector(BaseConnector):
    name = "telegram"

    def send(self, title: str, body: str, token: str = "",
             chat_id: str = "", **kwargs) -> bool:
        if not token or not chat_id:
            return False
        try:
            import httpx
            text = f"*{title}*\n{body}"
            httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=8.0,
            )
            return True
        except Exception:
            return False

    def test(self) -> bool:
        cfg = load_connectors().get("telegram", {})
        return self.send(
            "🕌 quran-cli", "Telegram notifications are working!",
            token=cfg.get("token",""), chat_id=cfg.get("chat_id","")
        )

    def setup(self) -> dict:
        from rich.console import Console
        from rich.rule import Rule
        c = Console()
        c.print()
        c.print(Rule("[dim]Telegram Setup[/dim]", style="green"))
        c.print()
        c.print("  1. Open Telegram and search [@BotFather](https://t.me/BotFather)")
        c.print("  2. Send /newbot and follow instructions to get a [bold]Bot Token[/bold]")
        c.print("  3. Start a chat with your new bot")
        c.print("  4. Send a message to @userinfobot or @getMyIDBot to get your Chat ID")
        c.print()
        c.print("[dim]Bot token:[/dim] ", end="")
        token = input().strip()
        c.print("[dim]Chat ID:[/dim] ", end="")
        chat_id = input().strip()
        return {"enabled": True, "token": token, "chat_id": chat_id}

    def is_configured(self, cfg: dict) -> bool:
        return bool(cfg.get("token") and cfg.get("chat_id"))


# ── WhatsApp (Twilio) ─────────────────────────────────────────────────────────

class WhatsAppConnector(BaseConnector):
    name = "whatsapp"

    def send(self, title: str, body: str, sid: str = "",
             token: str = "", from_: str = "", to: str = "", **kwargs) -> bool:
        if not all([sid, token, from_, to]):
            return False
        try:
            import httpx
            import base64
            auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
            message = f"🕌 *{title}*\n{body}"
            httpx.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                data={
                    "From": f"whatsapp:{from_}",
                    "To":   f"whatsapp:{to}",
                    "Body": message,
                },
                headers={"Authorization": f"Basic {auth}"},
                timeout=10.0,
            )
            return True
        except Exception:
            return False

    def test(self) -> bool:
        cfg = load_connectors().get("whatsapp", {})
        return self.send(
            "quran-cli test", "WhatsApp notifications are working!",
            sid=cfg.get("sid",""), token=cfg.get("token",""),
            from_=cfg.get("from",""), to=cfg.get("to","")
        )

    def setup(self) -> dict:
        from rich.console import Console
        from rich.rule import Rule
        c = Console()
        c.print()
        c.print(Rule("[dim]WhatsApp Setup (Twilio)[/dim]", style="yellow"))
        c.print()
        c.print("  1. Create free account at [bold]twilio.com[/bold]")
        c.print("  2. Go to Console > Messaging > WhatsApp Sandbox")
        c.print("  3. Connect your phone to the sandbox by sending the join code")
        c.print()
        c.print("[dim]Account SID:[/dim] ", end="");   sid  = input().strip()
        c.print("[dim]Auth Token:[/dim] ", end="");    tok  = input().strip()
        c.print("[dim]From number (+1415...):[/dim] ", end=""); frm = input().strip()
        c.print("[dim]Your WhatsApp number:[/dim] ", end="");  to  = input().strip()
        return {"enabled": True, "sid": sid, "token": tok, "from": frm, "to": to}

    def is_configured(self, cfg: dict) -> bool:
        return bool(cfg.get("sid") and cfg.get("token") and cfg.get("to"))


# ── Gmail ─────────────────────────────────────────────────────────────────────

class GmailConnector(BaseConnector):
    name = "gmail"

    def send(self, title: str, body: str, from_: str = "",
             app_password: str = "", to: str = "", **kwargs) -> bool:
        if not all([from_, app_password, to]):
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🕌 {title}"
            msg["From"]    = from_
            msg["To"]      = to
            html = f"""<html><body style="font-family:monospace;background:#07090d;color:#d4cfc4;padding:24px">
<h2 style="color:#10b981">{title}</h2>
<p style="font-size:16px">{body}</p>
<p style="color:#4a5568;font-size:12px">— quran-cli</p>
</body></html>"""
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(from_, app_password)
                s.sendmail(from_, to, msg.as_string())
            return True
        except Exception:
            return False

    def test(self) -> bool:
        cfg = load_connectors().get("gmail", {})
        return self.send(
            "quran-cli test", "Gmail notifications are working!",
            from_=cfg.get("from",""), app_password=cfg.get("app_password",""),
            to=cfg.get("to","")
        )

    def setup(self) -> dict:
        from rich.console import Console
        from rich.rule import Rule
        c = Console()
        c.print()
        c.print(Rule("[dim]Gmail Setup[/dim]", style="bright_black"))
        c.print()
        c.print("  1. Go to [bold]myaccount.google.com → Security → 2-Step Verification[/bold]")
        c.print("  2. Then → [bold]App passwords[/bold]")
        c.print("  3. Generate an app password for 'Mail'")
        c.print()
        c.print("[dim]Your Gmail address:[/dim] ", end=""); frm = input().strip()
        c.print("[dim]App password:[/dim] ", end="");       pwd = input().strip()
        c.print("[dim]Send reminders to:[/dim] ", end=""); to  = input().strip()
        c.print("[dim]Mode (daily/prayer):[/dim] ", end=""); mode = input().strip() or "daily"
        return {"enabled": True, "from": frm, "app_password": pwd, "to": to, "mode": mode}

    def is_configured(self, cfg: dict) -> bool:
        return bool(cfg.get("from") and cfg.get("app_password") and cfg.get("to"))


# ── Webhook ───────────────────────────────────────────────────────────────────

class WebhookConnector(BaseConnector):
    name = "webhook"

    def send(self, title: str, body: str, url: str = "", **kwargs) -> bool:
        if not url:
            return False
        try:
            import httpx, datetime
            payload = {
                "type": kwargs.get("notification_type", "prayer"),
                "title": title,
                "body": body,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source": "quran-cli",
            }
            payload.update({k: v for k, v in kwargs.items()
                            if k in ("prayer_name", "time", "location")})
            httpx.post(url, json=payload, timeout=5.0)
            return True
        except Exception:
            return False

    def test(self) -> bool:
        cfg = load_connectors().get("webhook", {})
        return self.send("quran-cli test", "Webhook is connected!", url=cfg.get("url",""))

    def setup(self) -> dict:
        from rich.console import Console
        c = Console()
        c.print("[dim]Webhook URL (Discord/Slack/custom):[/dim] ", end="")
        url = input().strip()
        return {"enabled": True, "url": url}

    def is_configured(self, cfg: dict) -> bool:
        return bool(cfg.get("url"))


# ── Dispatcher ────────────────────────────────────────────────────────────────

ALL_CONNECTORS = {
    "desktop":  DesktopConnector(),
    "ntfy":     NtfyConnector(),
    "telegram": TelegramConnector(),
    "whatsapp": WhatsAppConnector(),
    "gmail":    GmailConnector(),
    "webhook":  WebhookConnector(),
}


def dispatch(title: str, body: str, **kwargs) -> None:
    """Send notification to all enabled connectors in parallel threads."""
    cfg = load_connectors()

    def _fire(name: str, connector: BaseConnector, ccfg: dict) -> None:
        try:
            connector.send(title, body, **ccfg, **kwargs)
        except Exception:
            pass

    threads = []
    for name, connector in ALL_CONNECTORS.items():
        ccfg = cfg.get(name, {})
        if not ccfg.get("enabled", name == "desktop"):
            continue
        if name != "desktop" and not connector.is_configured(ccfg):
            continue
        t = threading.Thread(target=_fire, args=(name, connector, ccfg), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=10)
