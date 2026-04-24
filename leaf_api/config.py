import os
from pathlib import Path

basedir = Path(__file__).parent.parent


class Config:
    """Base configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + str(basedir / "agentics.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "demo-secret-key")
    JWT_ALGORITHM = "RS256"

    API_TITLE = "Agentics Orders API"
    API_VERSION = "1.0.0"
    CACHE_TTL = 3600  # ETag cache validity in seconds

    # JWT keypair paths
    JWT_PRIVATE_KEY_PATH = basedir / "leaf_api" / "auth" / "keypair.pem"
    JWT_PUBLIC_KEY_PATH = basedir / "leaf_api" / "auth" / "public_key.pem"


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


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
