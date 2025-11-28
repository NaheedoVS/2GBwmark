import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import tempfile

# 1. SETUP LOGGING
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 2. CONFIGURATION
TOKEN = os.getenv("TOKEN")
WATERMARK_TEXT = "My Telegram Bot" # Change this to your desired text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I am ready! Send me a video to watermark."
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    status_msg = await context.bot.send_message(chat_id=chat_id, text="Video received. Downloading...")
    
    input_path = f"input_{chat_id}.mp4"
    output_path = f"output_{chat_id}.mp4"

    try:
        # --- DOWNLOAD ---
        video_file = await update.message.video.get_file()
        # Increased timeout allows large files to download without error
        await video_file.download_to_drive(input_path)
        
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=status_msg.message_id, 
            text="Processing video... (This takes time)"
        )

        # --- WATERMARK LOGIC (MoviePy) ---
        # 1. Load Video
        clip = VideoFileClip(input_path)
        
        # 2. Create Text Watermark
        # Note: If this fails on Heroku, it's usually missing ImageMagick.
        # We use a try/except for safety.
        try:
            txt_clip = TextClip(WATERMARK_TEXT, fontsize=50, color='white')
            txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(clip.duration)
            
            # 3. Composite
            video = CompositeVideoClip([clip, txt_clip])
            
            # 4. Write File (uses libx264 for compatibility)
            video.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
        except OSError as e:
            # Fallback if ImageMagick is missing on server
            logging.error(f"ImageMagick error: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Server config error: ImageMagick missing. Sending original.")
            os.rename(input_path, output_path)

        # --- UPLOAD ---
        await context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=status_msg.message_id, 
            text="Uploading finished video..."
        )
        
        await context.bot.send_video(
            chat_id=chat_id,
            video=open(output_path, 'rb'),
            caption="Here is your watermarked video!"
        )

    except Exception as e:
        logging.error(f"General Error: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"Error: {str(e)}")

    finally:
        # --- CLEANUP ---
        # Close clips to release memory
        try:
            if 'clip' in locals(): clip.close()
            if 'video' in locals(): video.close()
        except:
            pass
            
        # Remove files
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

if name == 'main':
    if not TOKEN:
        print("Error: TOKEN not found in environment variables!")
        exit(1)

    # --- THE NETWORK FIX ---
    # Increases timeouts to prevent Heroku crashes
    request_settings = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )

    application = ApplicationBuilder().token(TOKEN).request(request_settings).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    print("Bot is polling...")
    application.run_polling()
