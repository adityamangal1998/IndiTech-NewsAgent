#!/usr/bin/env python3
"""
Run script for Aditya Daily Digest Flask application
Uses Uvicorn ASGI server for better performance
"""

import uvicorn
from app import app
from asgiref.wsgi import WsgiToAsgi

# Wrap Flask app with ASGI
asgi_app = WsgiToAsgi(app)

if __name__ == "__main__":
    print("🚀 Starting Aditya Daily Digest...")
    print("📰 News dashboard will be available at: http://localhost:8000")
    print("🔄 News will be refreshed every 30 minutes")
    
    # Run with Uvicorn ASGI server
    uvicorn.run(
        asgi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
