# Notification System Updates and Fixes

This document outlines the changes and improvements made to the `quran-cli` notification system, focusing on enhanced reliability, accurate timezone handling for Telegram bot users, and improved testability.

## Summary of Changes

1.  **Telegram Bot Timezone Fix**: The Telegram bot's `/setlocation` command now accurately determines the timezone based on the provided latitude and longitude using the TimeAPI.io service. Previously, it defaulted to "UTC", which could lead to incorrect prayer times for users in different timezones.
2.  **Telegram Bot Scheduler Job Refactoring**: The `_send_prayer_reminders` function in `telegram_bot.py` has been refactored to use named asynchronous functions for APScheduler jobs instead of lambda functions. This improves the clarity, maintainability, and reliability of the scheduled tasks.
3.  **Ntfy.sh Test Dispatch Fix**: The `quran remind test` command now correctly dispatches notifications to ntfy.sh by passing the `phone_topic` to the `dispatch_all` function. This ensures that the test notification reaches the configured ntfy.sh channel.

## Detailed Changes

### 1. Telegram Bot Timezone Fix

**File**: `quran/bot/telegram_bot.py`

**Description**: The `setlocation` command in the Telegram bot was updated to fetch the correct timezone from `timeapi.io` when a user sets their location by city name or coordinates. This addresses a critical bug where the timezone was always set to "UTC", causing prayer times to be inaccurate.

**Code Snippet (before)**:
```python
                subs[chat_id].update({
                    "lat": lat, "lon": lon,
                    "city": name, "tz": "UTC"
                })
```

**Code Snippet (after)**:
```python
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
```

### 2. Telegram Bot Scheduler Job Refactoring

**File**: `quran/bot/telegram_bot.py`

**Description**: Anonymous `lambda` functions used for scheduling jobs within `_send_prayer_reminders` were replaced with explicitly named `async` functions. This change improves debugging, readability, and ensures better compatibility with `APScheduler`'s serialization requirements.

**Example (Prayer Notification - before)**:
```python
                        scheduler.add_job(
                            lambda c=chat_id, n=name, ci=city: asyncio.create_task(
                                _send(c, f"🕌 *{n}* — {ci}")
                            ),
                            "date", run_date=dt,
                            id=f"prayer_{chat_id}_{name}",
                            replace_existing=True,
                            misfire_grace_time=300,
                        )
```

**Example (Prayer Notification - after)**:
```python
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
```
Similar changes were applied to Sehri warning, Iftar, Laylatul Qadr, and Ayah of the Day notifications.

### 3. Ntfy.sh Test Dispatch Fix

**File**: `quran/commands/remind.py`

**Description**: The `remind_test` function was updated to correctly pass the `phone_topic` from the configuration to the `dispatch_all` function. This ensures that test notifications are sent to the user's configured ntfy.sh channel, allowing for proper verification of the ntfy.sh integration.

**Code Snippet (before)**:
```python
    dispatch("🕌 quran-cli Test", f"This is a test reminder from your terminal. Location: {city}")
```

**Code Snippet (after)**:
```python
    topic = cfg["remind"].get("phone_topic", "")
    dispatch("🕌 quran-cli Test", f"This is a test reminder from your terminal. Location: {city}", topic=topic)
```

## Impact

These changes significantly improve the accuracy and reliability of prayer time notifications, especially for Telegram bot users. The refactoring of scheduler jobs enhances code quality and maintainability, while the ntfy.sh test fix ensures that all notification channels can be properly tested.

## References

[1] TimeAPI.io. (n.d.). *Time Zone API*. Retrieved from [https://timeapi.io/](https://timeapi.io/)
