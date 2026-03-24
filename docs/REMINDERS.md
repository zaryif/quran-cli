# Quran CLI - Reminders & Fasting Alerts

`quran-cli` includes a powerful, customizable background daemon that sends push notifications to your desktop, phone, or Telegram for daily prayers and fasting (Sahur/Iftar) times.

## 🚀 Quick Setup Wizard

The easiest way to get started is to run the interactive setup wizard:
```bash
quran remind setup
```
Or you can access it from the main dashboard (`quran` -> **Reminder Setup Wizard**).

The wizard will ask you standard questions:
1. **Daily Prayers**: Which of the 5 prayers you want, how many minutes in advance, and if you want an Adhan sound.
2. **Fasting Alerts**: Enable countdowns for Sahur and alerts for Iftar, completely independent of Ramadan, so you can receive them for Sunnah fasting days.
3. **Start Daemon**: It will ask if you want to turn on the background monitor immediately.
4. **Link Phone**: It gives you a quick ntfy.sh QR code so you can receive alerts on your iPhone or Android.

## 🛠 Manual Commands

If you prefer to configure things manually or script them:

- **Start Daemon**: `quran remind on`
- **Stop Daemon**: `quran remind off`
- **Check Status**: `quran remind status`
- **Link Phone**: `quran remind phone`
- **Test Alerts**: `quran remind test`

### Checking Logs
The daemon runs quietly in the background. If you want to see what it's scheduling or if you encounter any issues, check the logs here:
`~/.local/share/quran-cli/daemon.log`

## 📱 Notification Channels
By default, `quran-cli` sends notifications as native desktop popups (macOS/Windows/Linux notifications). You can link other channels instantly using:
```bash
quran connect
```
- **ntfy.sh (Free App)**: Download the `ntfy` app on your phone, run `quran remind phone`, and scan the QR code to get cross-device push notifications instantly. No account required.
- **Telegram**: Run `quran connect telegram` and pass your bot token and chat ID to receive messages on Telegram.
