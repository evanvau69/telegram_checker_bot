import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # These THREE are required for the BOT itself
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    @staticmethod
    def check():
        if not Config.API_ID:
            return False, "API_ID missing in .env file"
        if not Config.API_HASH:
            return False, "API_HASH missing in .env file"
        if not Config.BOT_TOKEN:
            return False, "BOT_TOKEN missing in .env file"
        return True, "All credentials are set"
