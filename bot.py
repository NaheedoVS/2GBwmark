import os
import logging
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

# 1. SETUP LOGGING (Kept from your old code)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

# 2. CONFIGURATION
# To support 2GB, we need API_ID and API_HASH from https://my.telegram.org/
# Add these to Heroku Config Vars
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
TOKEN = os.environ.get("TOKEN", "")

# 3. INITIALIZE CLIENT (Pyrogram Engine)
# This replaces ApplicationBuilder because this engine supports 2GB files.
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Bot is Online! Send me a video up to 2GB."
    )

@app.on_message(filters.video)
async def handle_video(client, message: Message):
    chat_id = message.chat.id
    
    # Notify user
    status_msg = await message.reply_text("Video received. Downloading (Supports 2GB)...")
    
    input_path = f"input_{chat_id}.mp4"
    output_path = f"output_{chat_id}.mp4"

    try:
        # --- DOWNLOAD ---
        # Pyrogram downloads large files efficiently
        await message.download(file_name=input_path)
        
        await status_msg.edit_text("Processing video... (Low-RAM Mode)")

        # --- PROCESS VIDEO (FFmpeg Subprocess) ---
        # We run this outside Python to prevent memory crashes (The Fix)
        command = [
            'ffmpeg', '-y', 
            '-i', input_path,
            '-vf', "drawtext=text='My Telegram Bot':fontcolor=white:fontsize=30:x=20:y=20",
            '-c:a', 'copy',          # Copy audio (fast)
            '-preset', 'ultrafast',  # Crucial for Heroku speed
            output_path
        ]
        
        # Execute command
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg Error: {stderr.decode()}")

        await status_msg.edit_text("Uploading processed video...")

        # --- UPLOAD ---
        await message.reply_video(
            video=output_path, 
            caption="Here is your video!"
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"Error: {str(e)}")

    finally:
        # --- CLEANUP ---
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

if name == "main":
    if not TOKEN or not API_ID:
        print("Error: API_ID, API_HASH, and TOKEN are required in Config Vars!")
        exit(1)

    print("Bot is starting polling...")
    app.run()
