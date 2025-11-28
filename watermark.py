import ffmpeg
import math
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from config import Config

logger = logging.getLogger(__name__)

# MODIFIED: Accepts 'color_rgb' argument
def create_text_watermark(text: str, output_path: str, color_rgb: tuple):
    try:
        # Use DejaVu font for Linux/Heroku/Docker
        font_path = "/usr/share/fonts/ttf-dejavu/DejaVuSans-Bold.ttf"
        try:
            font = ImageFont.truetype(font_path, Config.FONT_SIZE)
        except IOError:
            font = ImageFont.load_default()

        # Calculate Size
        dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        width, height = text_width + 30, text_height + 30
        img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # --- COLOR LOGIC ---
        # Combine the RGB color with the Opacity from config
        # Result is (R, G, B, A)
        final_color = color_rgb + (Config.OPACITY,)
        
        draw.text((15, 15), text, font=font, fill=final_color)

        img.save(output_path, "PNG")
        return True
    except Exception as e:
        logger.error(f"Error creating text image: {e}")
        return False

# ... (The rest of the file: get_video_info, process_video, split_video stays the same)
# Paste the previous logic for process_video and split_video here
# I will include process_video briefly to ensure you have the full file context if you copy-paste

def get_video_info(input_video: str):
    try:
        probe = ffmpeg.probe(input_video)
        duration = float(probe['format']['duration'])
        return duration
    except Exception: return 0

def process_video(input_video: str, output_video: str, watermark_img: str):
    try:
        probe = ffmpeg.probe(input_video)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)

        if not video_stream: raise ValueError("No video stream")

        in_file = ffmpeg.input(input_video)
        overlay_file = ffmpeg.input(watermark_img)

        video = in_file.overlay(
            overlay_file, 
            x=f"main_w-overlay_w-{Config.MARGIN_X}", 
            y=f"main_h-overlay_h-{Config.MARGIN_Y}"
        )

        output_args = {'vcodec': 'libx264', 'preset': 'veryfast', 'crf': 26, 'movflags': '+faststart'}

        if audio_stream:
            stream = ffmpeg.output(video, in_file.audio, output_video, **output_args)
        else:
            stream = ffmpeg.output(video, output_video, **output_args)

        stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        return True
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg Error: {e.stderr.decode('utf8')}")
        raise e

def split_video(input_path: str, output_dir: str):
    file_size = os.path.getsize(input_path)
    if file_size < Config.SPLIT_THRESHOLD_BYTES: return [input_path]
    duration = get_video_info(input_path)
    if duration == 0: return [input_path]

    num_parts = math.ceil(file_size / Config.SPLIT_THRESHOLD_BYTES)
    segment_time = int(duration / num_parts) + 1
    
    output_pattern = os.path.join(output_dir, "part_%03d.mp4")
    try:
        (
            ffmpeg.input(input_path)
            .output(output_pattern, c='copy', f='segment', segment_time=segment_time, reset_timestamps=1)
            .run(capture_stdout=True, capture_stderr=True)
        )
        parts = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith("part_")])
        return parts
    except ffmpeg.Error: return [input_path]
