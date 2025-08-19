# Quick Start Guide - Aditya Daily Digest

## 🚀 Quick Setup (5 minutes)

### Step 1: Prerequisites
- Python 3.8+ installed
- AWS Account with Bedrock access
- Tavily Search API key (sign up at [tavily.com](https://tavily.com))

### Step 2: Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd IndiTech-NewsAgent

# Run the setup script (Windows)
python setup.py
```

### Step 3: Configure Credentials
Edit the `.env` file with your credentials:
```env
AWS_ACCESS_KEY_ID=your_actual_aws_key
AWS_SECRET_ACCESS_KEY=your_actual_aws_secret
AWS_REGION=us-east-1
TAVILY_API_KEY=your_actual_tavily_key
```

### Step 4: Run the Application
```bash
# Using Python directly with Uvicorn
python app.py

# Or using the run script (Windows)
run.bat
# or
run.ps1

# For production
uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4
```

### Step 5: Access the Dashboard
Open your browser and go to: `http://localhost:5000`

---

## 🛠 Detailed Setup

### AWS Bedrock Setup
1. **Enable Bedrock**: Go to AWS Console → Bedrock → Model access
2. **Request Access**: Enable "Claude 3.5 Sonnet" model
3. **Create IAM User**: With `bedrock:*` permissions
4. **Get Credentials**: Access key and secret key

### Tavily API Setup
1. **Sign Up**: Go to [tavily.com](https://tavily.com)
2. **Get API Key**: From your dashboard
3. **Add to .env**: Copy the key to your `.env` file

### Project Structure
```
IndiTech-NewsAgent/
├── app.py              # Main Flask app
├── news_agent.py       # LangChain news agent
├── config.py          # Configuration
├── templates/
│   └── index.html     # Main dashboard
├── requirements.txt   # Dependencies
├── .env              # Your credentials
└── README.md         # Documentation
```

---

## 🔧 Configuration Options

### Environment Variables
```env
# Required
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
TAVILY_API_KEY=your_key

# Optional
AWS_REGION=us-east-1              # Default region
NEWS_REFRESH_INTERVAL=6           # Hours between refresh
MAX_NEWS_PER_CATEGORY=5           # Articles per category
FLASK_DEBUG=True                  # Debug mode
```

### News Categories
The app fetches news for:
- **Technology**: Latest tech innovations
- **Artificial Intelligence**: AI developments
- **Business**: Market and economic news
- **Startups**: Startup ecosystem updates
- **India Happenings**: Indian current affairs

---

## 🚦 Troubleshooting

### Common Issues

**1. "AWS credentials not found"**
```bash
# Check your .env file
cat .env
# Verify AWS credentials
aws sts get-caller-identity
```

**2. "Claude 3.5 Sonnet not available"**
- Go to AWS Console → Bedrock → Model access
- Request access to Claude 3.5 Sonnet
- Wait for approval (usually instant)

**3. "Tavily API error"**
- Verify your API key at tavily.com
- Check your usage limits

**4. "No news displayed"**
- Check the logs for errors
- Try manual refresh button
- Verify internet connectivity

### Debug Mode
Run with debug logging:
```bash
FLASK_DEBUG=True python app.py
```

### Test Installation
```bash
# Run the test suite
python test_app.py

# Run setup verification
python setup.py
```

---

## 🌟 Features

### AI-Powered Summarization
- Uses Claude 3.5 Sonnet for intelligent summarization
- Generates 2-3 sentence crisp summaries
- Professional and neutral tone

### Multiple News Sources
- RSS feeds from reputable sources
- Tavily Search API for real-time news
- Automatic deduplication

### Smart Caching
- Background refresh every 6 hours
- Persistent caching between restarts
- Manual refresh option

### Responsive UI
- Beautiful Bootstrap design
- Mobile-friendly interface
- Live loading indicators

---

## 📡 API Endpoints

### Web Interface
- `GET /` - Main dashboard
- `GET /refresh` - Manual refresh

### JSON API
- `GET /api/news` - All news as JSON
- `GET /api/news/Technology` - Technology news only
- `GET /health` - System health check

### Example API Response
```json
{
  "news": {
    "Technology": [
      {
        "title": "Latest AI Breakthrough...",
        "summary": "Researchers have developed...",
        "link": "https://...",
        "source": "TechCrunch",
        "published_date": "2024-01-15"
      }
    ]
  },
  "last_update": "2024-01-15T10:30:00"
}
```

---

## 🔄 Deployment

### Development
```bash
# With Uvicorn (recommended)
python app.py

# Or direct Uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

### Production (Linux/Mac)
```bash
# Direct Uvicorn with multiple workers
uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4

# With Gunicorn + Uvicorn workers
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000
```

---

## 📞 Support

### Getting Help
1. Check the logs for error details
2. Verify your configuration with `python setup.py`
3. Run tests with `python test_app.py`
4. Create an issue on GitHub

### Logs Location
- Console output when running `python app.py`
- Check `news_cache.json` for cached data

---

## 🎯 Next Steps

After setup:
1. **Customize**: Edit news categories in `news_agent.py`
2. **Enhance**: Add more RSS feeds or news sources
3. **Deploy**: Use Gunicorn + Nginx for production
4. **Monitor**: Set up logging and monitoring
5. **Scale**: Consider Redis for caching in production

---

*Happy news reading! 📰*
