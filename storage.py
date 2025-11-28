import json
import os
import logging
from config import Config

logger = logging.getLogger(__name__)

class Storage:
    def __init__(self):
        self.file_path = Config.DB_FILE
        self._data = {}
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self._data, f)
        except Exception:
            pass

    # --- WATERMARK TEXT ---
    def set_watermark(self, user_id, text):
        if str(user_id) not in self._data:
            self._data[str(user_id)] = {}
        
        # We store it as a dict now to hold multiple settings
        if isinstance(self._data[str(user_id)], str):
            # Convert old string format to new dict format if needed
            self._data[str(user_id)] = {"text": text, "color": Config.DEFAULT_COLOR}
        else:
            self._data[str(user_id)]["text"] = text
            
        self._save()

    def get_watermark(self, user_id):
        user_data = self._data.get(str(user_id), {})
        if isinstance(user_data, str): return user_data # Handle old format
        return user_data.get("text", Config.DEFAULT_WATERMARK)

    # --- NEW: COLOR SETTINGS ---
    def set_color(self, user_id, color_name):
        if str(user_id) not in self._data:
            self._data[str(user_id)] = {}
            
        # Handle old string format upgrade
        if isinstance(self._data[str(user_id)], str):
             self._data[str(user_id)] = {"text": self._data[str(user_id)], "color": color_name}
        else:
            self._data[str(user_id)]["color"] = color_name
        
        self._save()

    def get_color(self, user_id):
        user_data = self._data.get(str(user_id), {})
        if isinstance(user_data, str): return Config.DEFAULT_COLOR
        return user_data.get("color", Config.DEFAULT_COLOR)

db = Storage()
