import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Credentials (MUST HAVE ALL THREE)
    API_ID = int(os.getenv("API_ID", 0))          # From my.telegram.org
    API_HASH = os.getenv("API_HASH", "")          # From my.telegram.org
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")        # From @BotFather
    
    # Validation
    @classmethod
    def validate(cls):
        missing = []
        if not cls.API_ID:
            missing.append("API_ID")
        if not cls.API_HASH:
            missing.append("API_HASH")
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        
        if missing:
            print(f"❌ Missing environment variables: {', '.join(missing)}")
            print("Please set them in .env file")
            return False
        return True
