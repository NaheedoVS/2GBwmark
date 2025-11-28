#!/bin/sh

# 1. Start Telegram Bot API Local Server (Background)
# We use the env vars provided by Heroku Config Vars
echo "Starting Local Telegram Bot API Server..."
telegram-bot-api --api-id=${TELEGRAM_API_ID} --api-hash=${TELEGRAM_API_HASH} --local &

# 2. Wait 5 seconds to ensure server is ready
sleep 5

# 3. Start Python Bot (Foreground)
echo "Starting Python Bot..."
python3 bot.py
