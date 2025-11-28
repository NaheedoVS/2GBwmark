import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Credentials
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Local Server URL (Keep as localhost for Heroku Container / VPS)
    BASE_URL = "http://localhost:8081/bot"
    
    # Limits
    MAX_FILE_SIZE_MB = 2000
    SPLIT_THRESHOLD_BYTES = 1.95 * 1024 * 1024 * 1024
    
    # Timeouts
    READ_TIMEOUT = 3600
    WRITE_TIMEOUT = 3600
    CONNECT_TIMEOUT = 60

    DB_FILE = "user_data.json"
    
    # Default Settings
    DEFAULT_WATERMARK = "@WatermarkedBot"
    DEFAULT_COLOR = "White" # Default color name
    
    FONT_SIZE = 40
    OPACITY = 200
    MARGIN_X = 25
    MARGIN_Y = 25
    
    # --- NEW: AVAILABLE COLORS (Name: RGB Tuple) ---
    COLORS = {
        "White":  (255, 255, 255),
        "Red":    (255, 0, 0),
        "Black":  (0, 0, 0),
        "Blue":   (0, 0, 255),
        "Green":  (0, 255, 0),
        "Yellow": (255, 255, 0),
        "Orange": (255, 165, 0),
        "Purple": (128, 0, 128)
    }

