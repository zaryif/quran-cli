# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the entire project 
COPY . .

# Install the project and its dependencies (including bot extras)
RUN pip install --no-cache-dir -e ".[connectors]"

# Set the default command to start the Telegram Bot
CMD ["python", "-m", "quran.bot.telegram_bot"]
