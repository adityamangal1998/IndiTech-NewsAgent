"""
Configuration module for the Aditya Daily Digest Flask app
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # API Keys
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    
    # Application Settings
    NEWS_REFRESH_INTERVAL = int(os.getenv('NEWS_REFRESH_INTERVAL', 6))  # hours
    MAX_NEWS_PER_CATEGORY = int(os.getenv('MAX_NEWS_PER_CATEGORY', 5))
    
    # Cache Settings
    CACHE_FILE = 'news_cache.json'
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'TAVILY_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    FLASK_ENV = 'development'
    FLASK_DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    FLASK_ENV = 'production'
    FLASK_DEBUG = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
