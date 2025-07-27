import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MySQL Database Configuration for WAMPP
    # Default WAMPP MySQL settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or '3306'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''  # Default WAMPP has no password
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'insuremyway'
    
    # Construct the MySQL URI
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # Use SQLite for development/testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///insuremyway.db'
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use MySQL for production
    # In production, you should set these environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
