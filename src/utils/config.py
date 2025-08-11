"""
Configuration management for the application
"""

import os
from pathlib import Path

class Config:
    """Application configuration"""
    
    # Application info
    APP_NAME = "Riftbound TCG Collection Management"
    APP_VERSION = "1.0.0"
    ORGANIZATION = "celeste-co"
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    CARD_DATA_DIR = DATA_DIR / "card_data"
    CARD_IMG_DIR = DATA_DIR / "card_img"
    RESOURCES_DIR = BASE_DIR / "src" / "resources"
    
    # Database
    DATABASE_PATH = BASE_DIR / "collection.db"
    
    # API Configuration
    CARDMARKET_API_BASE_URL = "https://api.cardmarket.com/ws/v2.0"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all necessary directories exist"""
        directories = [
            cls.DATA_DIR,
            cls.CARD_DATA_DIR,
            cls.CARD_IMG_DIR,
            cls.RESOURCES_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_card_data_files(cls):
        """Get list of card data JSON files"""
        if cls.CARD_DATA_DIR.exists():
            return list(cls.CARD_DATA_DIR.glob("*.json"))
        return []
    
    @classmethod
    def get_card_image_files(cls):
        """Get list of card image files"""
        if cls.CARD_IMG_DIR.exists():
            return list(cls.CARD_IMG_DIR.rglob("*.webp"))
        return []
