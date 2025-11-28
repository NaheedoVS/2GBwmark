import os
import logging
import asyncio
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, # NEW
    filters
)
from telegram.request import HTTPXRequest

from config import Config
from storage import db
import watermark

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Video Watermark Bot**\n\n"
        "Send a video (Max 2GB) to start.\n"
        "Commands:\n"
        "/setwatermark <text> - Change text\n"
        "/setcolor - Change watermark color 🎨",
        parse_mode='Markdown'
    )

async def set_watermark_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /setwatermark <text>")
        return
    text = " ".join(context.args)
    db.set_watermark(user_id, text)
    await update.message.reply_text(f"✅ Watermark set: `{text}`", parse_mode='Markdown')

# --- NEW: COLOR MENU HANDLERS ---

async def set_color_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the color selection menu"""
    keyboard = []
    row = []
    # Create buttons from Config.COLORS
    for color_name in Config.COLORS.keys():
        # Callback data is "color:Red", "color:Blue", etc.
        btn = InlineKeyboardButton(f"🎨 {color_name}", callback_data=f"color:{color_name}")
        row.append(btn)
        if len(row) == 2: # 2 buttons per row
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎨 **Choose a color for your watermark:**", reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the button click"""
    query = update.callback_query
    await query.answer() # Acknowledge the click

    data = query.data
    if data.startswith("color:"):
        color_name = data.split(":")[1]
        user_id = query.from_user.id
        
        # Save to DB
        db.set_color(user_id, color_name)
        
        await query.edit_message_text(f"✅ Color updated to **{color_name}**! 🎨", parse_mode='Markdown')

# --------------------------------

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.video:
        file_obj = update.message.video
    elif update.message.document and 'video' in update.message.document.mime_type:
        file_obj = update.message.document
    else:
        return

    status_msg = await update.message.reply_text("⏳ Downloading 2GB+ capable stream...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            input_path = os.path.join(temp_dir, "input.mp4")
            watermarked_path = os.path.join(temp_dir, "watermarked.mp4")
            watermark_img = os.path.join(temp_dir, "wm.png")

            new_file = await context.bot.get_file(file_obj.file_id)
            await new_file.download_to_drive(input_path)
            
            await status_msg.edit_text("⚙️ Processing...")

            # 1. Get User Preferences
            user_text = db.get_watermark(user_id)
            color_name = db.get_color(user_id)
            
            # 2. Get RGB value from Config (Default to White if error)
            color_rgb = Config.COLORS.get(color_name, (255, 255, 255))

            # 3. Create Watermark (Passing the color now)
            await asyncio.to_thread(watermark.create_text_watermark, user_text, watermark_img, color_rgb)

            # 4. Process
            await asyncio.to_thread(watermark.process_video, input_path, watermarked_path, watermark_img)

            # 5. Split & Upload
            await status_msg.edit_text("⬆️ Uploading...")
            final_files = await asyncio.to_thread(watermark.split_video, watermarked_path, temp_dir)

            count = len(final_files)
            for index, file_path in enumerate(final_files):
                caption = f"Here is your video! ({color_name})"
                if count > 1: caption = f"Part {index+1}/{count} ({color_name})"
                
                with open(file_path, 'rb') as f:
                    await update.message.reply_video(
                        video=f,
                        caption=caption,
                        read_timeout=Config.READ_TIMEOUT,
                        write_timeout=Config.WRITE_TIMEOUT
                    )

            await status_msg.delete()

        except Exception as e:
            logger.error(f"Error: {e}")
            await status_msg.edit_text("❌ Error processing video.")

def main():
    request = HTTPXRequest(
        connect_timeout=Config.CONNECT_TIMEOUT,
        read_timeout=Config.READ_TIMEOUT,
        write_timeout=Config.WRITE_TIMEOUT
    )

    application = (
        ApplicationBuilder()
        .token(Config.BOT_TOKEN)
        .base_url(Config.BASE_URL) 
        .request(request)
        .build()
    )

    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setwatermark", set_watermark_command))
    application.add_handler(CommandHandler("setcolor", set_color_command)) # NEW
    application.add_handler(CallbackQueryHandler(button_callback))         # NEW
    
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))

    print(f"Bot running on {Config.BASE_URL}...")
    application.run_polling()

if __name__ == '__main__':
    main()
