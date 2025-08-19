"""
Uvicorn configuration for Aditya Daily Digest
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Uvicorn configuration
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', 5000)}"
workers = int(os.getenv('WORKERS', 1))
worker_class = "uvicorn.workers.UvicornWorker"
reload = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
log_level = "info" if reload else "warning"
access_log = reload
timeout = 300  # 5 minutes timeout for long-running news fetches

# SSL Configuration (for production)
keyfile = os.getenv('SSL_KEYFILE')
certfile = os.getenv('SSL_CERTFILE')

# Application settings
app_module = "app:app"
