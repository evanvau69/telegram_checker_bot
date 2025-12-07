import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Required credentials
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # Bot settings
    MAX_NUMBERS_PER_REQUEST = 50
    CHECK_DELAY_SECONDS = 1.5
    
    @classmethod
    def validate(cls):
        """Validate all required credentials are set"""
        errors = []
        
        if not cls.API_ID or cls.API_ID == 0:
            errors.append("API_ID is missing or invalid")
        if not cls.API_HASH:
            errors.append("API_HASH is missing")
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is missing")
        
        if errors:
            return False, errors
        return True, "All credentials are valid"
