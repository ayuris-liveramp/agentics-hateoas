import os
from pathlib import Path

basedir = Path(__file__).parent.parent


class Config:
    """Base configuration for root app"""
    CHILD_API_URLS = os.environ.get("CHILD_API_URLS", "http://localhost:5000").split(",")
    CACHE_DIR = os.environ.get("CACHE_DIR", str(basedir / "cache"))
    CACHE_TTL = 3600  # ETag cache validity in seconds


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    CACHE_DIR = "/tmp/agentics_cache"


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
