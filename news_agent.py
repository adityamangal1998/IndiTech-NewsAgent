import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Compatibility fix for Python 3.13+
try:
    import cgi
except ImportError:
    # For Python 3.13+ where cgi module was removed
    import html
    class cgi:
        @staticmethod
        def escape(s, quote=False):
            return html.escape(s, quote=quote)

import feedparser
import requests
from bs4 import BeautifulSoup

from langchain_aws import ChatBedrock
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    """Data class for news items"""
    title: str
    summary: str
    link: str
    category: str
    published_date: datetime
    source: str

class NewsAgent:
    """LangChain agent for fetching and summarizing news"""
    
    def __init__(self, aws_region: str = "us-east-1", tavily_api_key: str = None):
        self.aws_region = aws_region
        self.tavily_api_key = tavily_api_key
        
        # Initialize Claude 3.5 Sonnet via Bedrock
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:us-east-2:905418105552:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name=aws_region,
            model_kwargs={
                "max_tokens": 1000,
                "temperature": 0.3
            },
            # Add provider since we're using an ARN
            provider="anthropic"
        )
        
        # Initialize Tavily Search tool
        if tavily_api_key:
            self.search_tool = TavilySearchResults(
                api_key=tavily_api_key,
                max_results=5
            )
        else:
            self.search_tool = None
            logger.warning("Tavily API key not provided. Search functionality will be limited.")
        
        # News categories and their search terms
        self.categories = {
            "Technology": ["technology news", "tech innovations", "software development", "hardware"],
            "Artificial Intelligence": ["AI news", "machine learning", "artificial intelligence", "deep learning"],
            "Business": ["business news", "economy", "markets", "finance"],
            "Startups": ["startup news", "venture capital", "entrepreneurship", "new companies"],
            "India Happenings": ["India news", "Indian politics", "Indian economy", "India current affairs"]
        }
        
        # RSS feeds for reliable news sources
        self.rss_feeds = {
            "Technology": [
                "https://feeds.feedburner.com/TechCrunch",
                "https://www.wired.com/feed/rss",
                "https://techcrunch.com/feed/"
            ],
            "Artificial Intelligence": [
                "https://www.artificialintelligence-news.com/feed/",
                "https://machinelearningmastery.com/feed/"
            ],
            "Business": [
                "https://feeds.bloomberg.com/markets/news.rss",
                "https://www.business-standard.com/rss/home_page_top_stories.rss"
            ],
            "Startups": [
                "https://techcrunch.com/category/startups/feed/",
                "https://www.entrepreneur.com/latest.rss"
            ],
            "India Happenings": [
                "https://www.thehindu.com/news/national/feeder/default.rss",
                "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                "https://www.ndtv.com/india-news/rss"
            ]
        }
    
    def fetch_rss_news(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch news from RSS feeds for a given category"""
        news_items = []
        feeds = self.rss_feeds.get(category, [])
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:limit//len(feeds)]:
                    news_item = {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "description": entry.get("description", ""),
                        "published": entry.get("published", ""),
                        "source": feed.feed.get("title", "Unknown Source")
                    }
                    news_items.append(news_item)
                    
            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
                continue
        
        return news_items[:limit]
    
    def search_news_with_tavily(self, category: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for news using Tavily Search API"""
        if not self.search_tool:
            return []
        
        try:
            search_query = f"{query} news today latest"
            results = self.search_tool.invoke({"query": search_query})
            
            news_items = []
            for result in results[:limit]:
                news_item = {
                    "title": result.get("title", ""),
                    "link": result.get("url", ""),
                    "description": result.get("content", ""),
                    "published": datetime.now().isoformat(),
                    "source": "Tavily Search"
                }
                news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching with Tavily for {category}: {str(e)}")
            return []
    
    def summarize_article(self, title: str, content: str, category: str) -> str:
        """Summarize an article using Claude 3.5 Sonnet"""
        try:
            prompt = f"""
            You are a professional news summarizer. Please summarize the following news article in 2-3 crisp, informative sentences.
            
            Category: {category}
            Title: {title}
            Content: {content}
            
            Requirements:
            - Keep it concise but informative
            - Focus on the most important facts
            - Write in a professional, neutral tone
            - Ensure the summary is engaging and easy to read
            
            Summary:
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing article: {str(e)}")
            # Fallback to truncated content
            return content[:200] + "..." if len(content) > 200 else content
    
    def fetch_and_summarize_news(self, category: str, limit: int = 5) -> List[NewsItem]:
        """Fetch and summarize news for a specific category"""
        logger.info(f"Fetching news for category: {category}")
        
        # Fetch from RSS feeds
        rss_news = self.fetch_rss_news(category, limit)
        
        # Fetch from Tavily search if available
        tavily_news = []
        if self.search_tool and category in self.categories:
            for search_term in self.categories[category][:2]:  # Use first 2 search terms
                tavily_results = self.search_news_with_tavily(category, search_term, 2)
                tavily_news.extend(tavily_results)
        
        # Combine and deduplicate news items
        all_news = rss_news + tavily_news
        seen_titles = set()
        unique_news = []
        
        for item in all_news:
            title_normalized = item["title"].lower().strip()
            if title_normalized not in seen_titles and len(title_normalized) > 10:
                seen_titles.add(title_normalized)
                unique_news.append(item)
        
        # Summarize articles and create NewsItem objects
        summarized_news = []
        for item in unique_news[:limit]:
            try:
                # Get article content for summarization
                content_for_summary = item.get("description", item.get("title", ""))
                
                # Summarize the article
                summary = self.summarize_article(
                    item["title"], 
                    content_for_summary, 
                    category
                )
                
                # Parse published date
                published_date = datetime.now()
                if item.get("published"):
                    try:
                        # Try to parse the published date
                        import dateutil.parser
                        published_date = dateutil.parser.parse(item["published"])
                    except:
                        published_date = datetime.now()
                
                news_item = NewsItem(
                    title=item["title"],
                    summary=summary,
                    link=item["link"],
                    category=category,
                    published_date=published_date,
                    source=item.get("source", "Unknown")
                )
                
                summarized_news.append(news_item)
                
            except Exception as e:
                logger.error(f"Error processing news item: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {len(summarized_news)} news items for {category}")
        return summarized_news
    
    def fetch_all_news(self) -> Dict[str, List[NewsItem]]:
        """Fetch and summarize news for all categories"""
        all_news = {}
        
        for category in self.categories.keys():
            try:
                news_items = self.fetch_and_summarize_news(category, limit=5)
                all_news[category] = news_items
            except Exception as e:
                logger.error(f"Error fetching news for {category}: {str(e)}")
                all_news[category] = []
        
        return all_news

def create_news_agent(aws_region: str = None, tavily_api_key: str = None) -> NewsAgent:
    """Factory function to create a NewsAgent instance"""
    return NewsAgent(
        aws_region=aws_region or os.getenv("AWS_REGION", "us-east-1"),
        tavily_api_key=tavily_api_key or os.getenv("TAVILY_API_KEY")
    )
