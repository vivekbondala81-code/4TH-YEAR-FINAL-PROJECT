import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_key_4: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Get the first available API key
def get_gemini_api_key() -> str:
    """Get the first available Gemini API key"""
    keys = [
        settings.gemini_api_key,
        settings.gemini_api_key_2,
        settings.gemini_api_key_3,
        settings.gemini_api_key_4,
        os.environ.get("GEMINI_API_KEY", "")
    ]
    for key in keys:
        if key:
            return key
    return ""
