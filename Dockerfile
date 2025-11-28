# Start with the Official Telegram API Server (Alpine Linux)
FROM aiogram/telegram-bot-api:latest

# Switch to root user to install software
USER root

# Install Python3, Pip, FFmpeg, and Fonts
# (We need font-dejavu for the Watermark Text)
RUN apk update && \
    apk add --no-cache python3 py3-pip ffmpeg font-dejavu

# Set working directory
WORKDIR /app

# Copy Requirements first (for cache efficiency)
COPY requirements.txt .

# Install Python Dependencies
# (Alpine requires --break-system-packages for system-wide pip install)
RUN pip3 install --break-system-packages -r requirements.txt

# Copy All Project Files (bot.py, config.py, run.sh, etc.)
COPY . .

# CRITICAL: Fix line endings and permissions for run.sh
# (This prevents the "File not found" error if saved on Windows)
RUN sed -i 's/\r$//' run.sh && \
    chmod +x run.sh

# Environment Setup for Local API Server
ENV TELEGRAM_WORK_DIR="/app/telegram-data"
ENV TELEGRAM_TEMP_DIR="/app/telegram-temp"
RUN mkdir -p $TELEGRAM_WORK_DIR $TELEGRAM_TEMP_DIR

# Expose Port (Internal)
EXPOSE 8081

# Command to run the script
CMD ["./run.sh"]

