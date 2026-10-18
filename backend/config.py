import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_key_4: str = ""
    gemini_api_key_5: str = ""
    gemini_api_key_6: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def get_gemini_api_keys() -> List[str]:
    """Return every configured Gemini API key, preserving order and removing duplicates."""
    candidates = [
        settings.gemini_api_key,
        settings.gemini_api_key_2,
        settings.gemini_api_key_3,
        settings.gemini_api_key_4,
        settings.gemini_api_key_5,
        settings.gemini_api_key_6,
        os.environ.get("GEMINI_API_KEY", ""),
    ]

    keys: List[str] = []
    for key in candidates:
        if key and key not in keys and "your_gemini_api_key" not in key:
            keys.append(key)
    return keys


def get_gemini_api_key() -> str:
    """Get the first available Gemini API key."""
    keys = get_gemini_api_keys()
    return keys[0] if keys else ""
