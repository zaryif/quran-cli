# ☁️ How to get 24/7 Telegram Prayer Reminders for Free

If you want your Telegram bot to send you prayer times and fasting alerts **even when your laptop is turned off**, you need to host the bot in the cloud.

Because `quran-cli` is so lightweight, you can host your personal bot on a cloud provider like **Koyeb** for absolutely **100% free, forever.**

Here is the step-by-step guide. It takes exactly 2 minutes.

---

## 🚀 1-Click Deploy on Koyeb (Recommended)

Koyeb offers a free "Eco" tier that runs 24/7. Because we included a `Dockerfile` in this repository, Koyeb will build and run your bot automatically.

1. **Sign up**: Go to [app.koyeb.com](https://app.koyeb.com/) and sign up with your GitHub account.
2. **Create a Service**: Click **Create Web Service**.
3. **Select GitHub**: Choose GitHub as your deployment method.
4. **Enter this Repository**: If you forked `quran-cli`, select your fork. If not, you can enter the public repository URL: `https://github.com/zaryif/quran-cli`.
5. **Set the Token**: Scroll down to **Environment Variables**.
   - Click **Add Variable**.
   - **Key**: `TELEGRAM_BOT_TOKEN`
   - **Value**: Paste the token you got from `@BotFather` on Telegram.
6. **Set the Instance Type**: Ensure the **Free / Eco** tier is selected (it should be selected by default).
7. **Deploy**: Click **Deploy**.

That's it! 
Within 60 seconds, your bot will say "Healthy" on Koyeb. Your Telegram bot is now running in the cloud. It will automatically calculate prayer times every day, push daily ayahs, and send Sahur/Iftar countdowns exactly on time.

### How to Change Your Location in the Cloud
Since the bot is running in a cloud data center (likely in Europe or the US), its default location might be wrong.

1. Open Telegram on your phone.
2. Go to your bot's chat.
3. Send the command: `/setlocation Your City` (e.g., `/setlocation Dhaka` or `/setlocation London`).
4. (Optional) Send `/setmethod Karachi` to change the prayer calculation method.
5. Send `/pray` to verify the times are correct!

---

## Alternative: Render.com

If you prefer Render, you can also deploy it as a **Background Worker**:
1. Connect Render to your GitHub.
2. Create a **New Background Worker**.
3. Select the `quran-cli` repository.
4. Set the Environment: `Docker`.
5. Add the Environment Variable: `TELEGRAM_BOT_TOKEN`.
6. Deploy!
*(Note: Render's free tier sometimes spins down or consumes monthly free hours, which is why Koyeb is highly recommended for 24/7 uptime).*
