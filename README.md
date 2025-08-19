# Aditya Daily Digest

A Flask web application that aggregates and summarizes news from multiple categories using AWS Bedrock Claude 3.5 Sonnet and LangChain.

## Features

- **AI-Powered Summarization**: Uses AWS Bedrock Claude 3.5 Sonnet via LangChain for intelligent news summarization
- **Multi-Category News**: Covers Technology, AI, Business, Startups, and India Happenings
- **Automated Refresh**: Background scheduler refreshes news every 6 hours
- **Responsive UI**: Bootstrap-based responsive design with beautiful cards
- **Real-time Updates**: Manual refresh capability with live feedback
- **Multiple News Sources**: Integrates RSS feeds and Tavily Search API
- **Caching**: Persistent caching system for better performance

## Tech Stack

- **Backend**: Flask, Python 3.8+, Uvicorn ASGI Server
- **AI/ML**: LangChain, AWS Bedrock (Claude 3.5 Sonnet)
- **News Sources**: RSS feeds, Tavily Search API
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Scheduling**: APScheduler
- **Data**: JSON caching, feedparser

## Prerequisites

1. **AWS Account** with Bedrock access to Claude 3.5 Sonnet
2. **Tavily Search API** key (for enhanced news search)
3. **Python 3.8+**

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd IndiTech-NewsAgent
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   
   Copy `.env` file and fill in your credentials:
   ```env
   # AWS Credentials
   AWS_ACCESS_KEY_ID=your_aws_access_key_here
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
   AWS_REGION=us-east-1

   # Tavily Search API Key
   TAVILY_API_KEY=your_tavily_api_key_here

   # Optional: News API Key
   NEWS_API_KEY=your_news_api_key_here

   # Flask Configuration
   FLASK_ENV=development
   FLASK_DEBUG=True
   NEWS_REFRESH_INTERVAL=6
   ```

## Running the Application

1. **Start the Flask app with Uvicorn**:
   ```bash
   python app.py
   ```

2. **Or run with Uvicorn directly (production)**:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4
   ```

3. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## API Endpoints

- `GET /` - Main dashboard
- `GET /refresh` - Manual news refresh
- `GET /api/news` - Get all news as JSON
- `GET /api/news/<category>` - Get news for specific category
- `GET /health` - Health check endpoint

## Project Structure

```
IndiTech-NewsAgent/
├── app.py                 # Main Flask application
├── news_agent.py          # LangChain news agent
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── templates/
│   └── index.html        # Main dashboard template
├── news_cache.json       # News cache file (auto-generated)
└── README.md             # This file
```

## Configuration

### AWS Bedrock Setup

1. Ensure your AWS account has access to Bedrock
2. Enable Claude 3.5 Sonnet model in your region
3. Configure IAM permissions for Bedrock access

### Tavily Search API

1. Sign up at [Tavily](https://tavily.com/)
2. Get your API key
3. Add it to your `.env` file

## News Categories

The application covers these categories:

1. **Technology** - Latest tech news and innovations
2. **Artificial Intelligence** - AI developments and research
3. **Business** - Market news and economic updates
4. **Startups** - Startup ecosystem and venture capital
5. **India Happenings** - Indian news and current affairs

## Features in Detail

### AI Summarization
- Uses Claude 3.5 Sonnet for intelligent summarization
- Generates 2-3 sentence crisp summaries
- Maintains professional and neutral tone

### News Sources
- RSS feeds from reputable sources
- Tavily Search API for real-time news
- Automatic deduplication of articles

### Scheduling
- Background refresh every 6 hours (configurable)
- Manual refresh option
- Persistent caching between restarts

### User Interface
- Responsive Bootstrap design
- Beautiful gradient backgrounds
- Category-wise organization
- Live loading indicators

## Deployment

### Development
```bash
# Using the app script with Uvicorn
python app.py

# Or using run scripts
run.bat          # Windows batch file
run.ps1          # PowerShell script
```

### Production
```bash
# Direct Uvicorn (recommended)
uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4

# Using production scripts
run_production.bat    # Windows batch file
run_production.ps1    # PowerShell script

# With Gunicorn + Uvicorn workers (Linux/Mac)
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000
```

### Other Deployment Options
Consider using:
- **Nginx** for reverse proxy
- **Cloud platforms** for hosting (AWS EC2, Heroku, etc.)

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**:
   - Verify AWS credentials in `.env`
   - Check Bedrock access permissions
   - Ensure Claude 3.5 Sonnet is available in your region

2. **Tavily API Error**:
   - Verify API key is correct
   - Check API quota/limits

3. **No News Displayed**:
   - Check logs for errors
   - Verify internet connectivity
   - Try manual refresh

### Logs
Check application logs for detailed error information:
```bash
python app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the logs for error details
2. Verify your configuration
3. Create an issue on the repository

## Future Enhancements

- [ ] User authentication and personalization
- [ ] Email/SMS notifications
- [ ] More news categories
- [ ] Advanced filtering options
- [ ] Social media integration
- [ ] Mobile app
- [ ] Analytics dashboard
