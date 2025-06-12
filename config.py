"""
Configuration settings for AnkiVoice application.
"""

import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """Application configuration."""
    
    # Database settings
    DATABASE_PATH = "ankivoice.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # Ollama settings
    OLLAMA_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "gemma3:4b"
    AVAILABLE_MODELS = ["gemma3:4b"]  # Only gemma3:4b as requested
    
    # LLM parameters
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 1000
    LLM_TIMEOUT = 30  # seconds
    
    # Spaced repetition settings
    SR_INITIAL_INTERVAL = 1  # days
    SR_EASE_FACTOR_MIN = 1.3
    SR_EASE_FACTOR_MAX = 4.0
    SR_EASE_FACTOR_DEFAULT = 2.5
    SR_INTERVAL_MULTIPLIER = 2.5
    SR_MAX_INTERVAL = 365  # days
    
    # Question generation settings
    DEFAULT_QUESTIONS_PER_CARD = 3
    MAX_QUESTIONS_PER_CARD = 10
    QUESTION_GENERATION_TIMEOUT = 15  # seconds
    
    # Answer evaluation settings
    ANSWER_EVALUATION_TIMEOUT = 10  # seconds
    CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for automatic evaluation
    
    # UI settings
    STREAMLIT_PAGE_TITLE = "AnkiVoice - AI-Powered Flashcards"
    STREAMLIT_PAGE_ICON = "🧠"
    STREAMLIT_LAYOUT = "wide"
    
    # Audio settings (for future implementation)
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHUNK_SIZE = 1024
    AUDIO_FORMAT = "wav"
    
    # Performance settings
    CACHE_SIZE = 100  # Number of items to cache
    BATCH_SIZE = 10   # Batch size for processing
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_database_path(cls) -> Path:
        """Get the full path to the database file."""
        return Path(cls.DATABASE_PATH).absolute()
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        db_path = cls.get_database_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_ollama_config(cls) -> Dict[str, Any]:
        """Get Ollama configuration dictionary."""
        return {
            "host": cls.OLLAMA_HOST,
            "model": cls.DEFAULT_MODEL,
            "temperature": cls.LLM_TEMPERATURE,
            "max_tokens": cls.LLM_MAX_TOKENS,
            "timeout": cls.LLM_TIMEOUT
        }
    
    @classmethod
    def get_sr_config(cls) -> Dict[str, Any]:
        """Get spaced repetition configuration dictionary."""
        return {
            "initial_interval": cls.SR_INITIAL_INTERVAL,
            "ease_factor_min": cls.SR_EASE_FACTOR_MIN,
            "ease_factor_max": cls.SR_EASE_FACTOR_MAX,
            "ease_factor_default": cls.SR_EASE_FACTOR_DEFAULT,
            "interval_multiplier": cls.SR_INTERVAL_MULTIPLIER,
            "max_interval": cls.SR_MAX_INTERVAL
        }


# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    LLM_TIMEOUT = 60  # Longer timeout for production


# Select configuration based on environment
ENV = os.getenv("ANKIVOICE_ENV", "development").lower()
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()