import os
import json
import logging
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

# Python 3.13 compatibility: Add cgi module shim
if sys.version_info >= (3, 13):
    import cgi_compat
    sys.modules['cgi'] = cgi_compat
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
import atexit

# Import the super fast news agent
from super_fast_news_agent import create_super_fast_news_agent, NewsItem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# ASGI wrapper for Uvicorn compatibility
from asgiref.wsgi import WsgiToAsgi
asgi_app = WsgiToAsgi(app)

# Global variables for caching news data
news_cache = {}
last_update = None

# Initialize news agent
news_agent = None

def initialize_news_agent():
    """Initialize the news agent with AWS and API credentials"""
    global news_agent
    try:
        news_agent = create_super_fast_news_agent(
            use_ai_summary=True,
            aws_region=os.getenv("AWS_REGION")
        )
        logger.info("Super fast news agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize news agent: {str(e)}")
        news_agent = None

def refresh_news():
    """Fetch fresh news for all categories"""
    global news_cache, last_update
    
    if not news_agent:
        logger.error("News agent not initialized. Cannot fetch news.")
        return
    
    try:
        logger.info("Starting super fast news refresh...")
        fresh_news = news_agent.fetch_all_news_super_fast()
        
        # Convert NewsItem objects to dictionaries for JSON serialization
        news_cache = {}
        for category, items in fresh_news.items():
            news_cache[category] = [
                {
                    'title': item.title,
                    'summary': item.summary,
                    'link': item.link,
                    'category': item.category,
                    'published_date': item.published_date.isoformat(),
                    'source': item.source
                }
                for item in items
            ]
        
        last_update = datetime.now()
        logger.info(f"News refresh completed at {last_update}")
        
        # Save to cache file for persistence
        save_news_cache()
        
    except Exception as e:
        logger.error(f"Error during news refresh: {str(e)}")

def save_news_cache():
    """Save news cache to file"""
    try:
        cache_data = {
            'news': news_cache,
            'last_update': last_update.isoformat() if last_update else None
        }
        with open('news_cache.json', 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info("News cache saved to file")
    except Exception as e:
        logger.error(f"Error saving news cache: {str(e)}")

def load_news_cache():
    """Load news cache from file"""
    global news_cache, last_update
    try:
        if os.path.exists('news_cache.json'):
            with open('news_cache.json', 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                news_cache = cache_data.get('news', {})
                if cache_data.get('last_update'):
                    last_update = datetime.fromisoformat(cache_data['last_update'])
                logger.info("News cache loaded from file")
        else:
            logger.info("No cache file found, starting fresh")
    except Exception as e:
        logger.error(f"Error loading news cache: {str(e)}")

@app.route('/')
def index():
    """Main dashboard route"""
    global news_cache, last_update
    
    # If cache is empty or too old, try to refresh (but don't block the request)
    if not news_cache or not last_update or (datetime.now() - last_update).total_seconds() / 3600 > 12:
        logger.info("Cache is empty or old, will refresh in background...")
        # Don't block the request - let the user see the page even if cache is empty
        # The background scheduler will handle refreshing
    
    # Calculate time since last update
    time_since_update = None
    if last_update:
        delta = datetime.now() - last_update
        if delta.days > 0:
            time_since_update = f"{delta.days} day(s) ago"
        elif delta.seconds > 3600:
            time_since_update = f"{delta.seconds // 3600} hour(s) ago"
        else:
            time_since_update = f"{delta.seconds // 60} minute(s) ago"
    
    return render_template('index.html', 
                         news_data=news_cache, 
                         last_update=last_update,
                         time_since_update=time_since_update)

@app.route('/refresh')
def manual_refresh():
    """Manual refresh endpoint"""
    try:
        if not news_agent:
            initialize_news_agent()
        
        if news_agent:
            refresh_news()
            return jsonify({
                'status': 'success',
                'message': 'News refreshed successfully',
                'last_update': last_update.isoformat() if last_update else None
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'News agent not initialized. Check your AWS and API credentials.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error during manual refresh: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error refreshing news: {str(e)}'
        }), 500

@app.route('/api/news')
def api_news():
    """API endpoint to get news data as JSON"""
    return jsonify({
        'news': news_cache,
        'last_update': last_update.isoformat() if last_update else None
    })

@app.route('/api/news/<category>')
def api_news_category(category):
    """API endpoint to get news for a specific category"""
    category_news = news_cache.get(category, [])
    return jsonify({
        'category': category,
        'news': category_news,
        'count': len(category_news)
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'news_agent_initialized': news_agent is not None,
        'cache_size': sum(len(items) for items in news_cache.values()),
        'last_update': last_update.isoformat() if last_update else None
    })

@app.route('/test')
def test_route():
    """Simple test route"""
    return "<h1>Flask App is Working!</h1><p>Server is running properly.</p>"

@app.route('/simple')
def simple_dashboard():
    """Simple dashboard route for testing"""
    global news_cache, last_update
    
    # Calculate time since last update
    time_since_update = None
    if last_update:
        delta = datetime.now() - last_update
        if delta.days > 0:
            time_since_update = f"{delta.days} day(s) ago"
        elif delta.total_seconds() > 3600:
            time_since_update = f"{int(delta.total_seconds() // 3600)} hour(s) ago"
        else:
            time_since_update = f"{int(delta.total_seconds() // 60)} minute(s) ago"
    
    return render_template('simple.html', 
                         news_data=news_cache, 
                         last_update=last_update,
                         time_since_update=time_since_update)

def setup_scheduler():
    """Setup background scheduler for automatic news refresh"""
    refresh_interval = int(os.getenv('NEWS_REFRESH_INTERVAL', 6))  # Default 6 hours
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=refresh_news,
        trigger=IntervalTrigger(hours=refresh_interval),
        id='news_refresh_job',
        name='Refresh news every {} hours'.format(refresh_interval),
        replace_existing=True
    )
    
    try:
        scheduler.start()
        logger.info(f"Scheduler started: News will refresh every {refresh_interval} hours")
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")

@app.route('/debug')
def debug_data():
    """Debug route to view raw news data"""
    global news_cache, last_update
    debug_info = {
        'last_update': last_update.isoformat() if last_update else None,
        'news_cache_size': len(news_cache) if news_cache else 0,
        'news_data': news_cache
    }
    return jsonify(debug_info)

if __name__ == '__main__':
    # Load existing cache
    load_news_cache()
    
    # Initialize news agent
    initialize_news_agent()
    
    # Setup automatic refresh scheduler
    setup_scheduler()
    
    # Schedule initial news fetch if cache is empty (non-blocking)
    if not news_cache and news_agent:
        logger.info("Cache is empty, scheduling initial news fetch...")
        # Use the scheduler to fetch news in background instead of blocking startup
        import threading
        threading.Thread(target=refresh_news, daemon=True).start()
    
    # Run Flask app with Uvicorn
    import uvicorn
    
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting Uvicorn server on {host}:{port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info("Open your browser and go to: http://localhost:5000")
    
    uvicorn.run(
        "app:asgi_app",
        host=host,
        port=port,
        reload=debug_mode,
        log_level="info" if debug_mode else "warning",
        access_log=debug_mode
    )
