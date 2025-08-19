import os
import json
import logging
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Compatibility fix for Python 3.13+
import sys
if sys.version_info >= (3, 13):
    import html
    import urllib.parse
    
    class MockCGI:
        @staticmethod
        def escape(s, quote=False):
            return html.escape(s, quote=quote)
        
        @staticmethod
        def parse_header(line):
            """Parse a Content-type like header."""
            parts = line.split(';')
            main_type = parts[0].strip()
            pdict = {}
            for p in parts[1:]:
                i = p.find('=')
                if i >= 0:
                    name = p[:i].strip().lower()
                    value = p[i+1:].strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    pdict[name] = value
            return main_type, pdict
        
        @staticmethod
        def parse_qs(qs, keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace'):
            return urllib.parse.parse_qs(qs, keep_blank_values, strict_parsing, encoding, errors)
    
    sys.modules['cgi'] = MockCGI()

import requests
import feedparser
from bs4 import BeautifulSoup

from langchain_aws import ChatBedrock
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

class OptimizedNewsAgent:
    """Optimized news agent using RSS feeds with parallel processing"""
    
    def __init__(self, aws_region: str = "us-east-1"):
        self.aws_region = aws_region
        
        # Initialize Claude 3.5 Sonnet via Bedrock with specific model ARN
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:us-east-2:905418105552:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name="us-east-2",
            model_kwargs={
                "max_tokens": 500,  # Reduced for faster processing
                "temperature": 0.1,
                "anthropic_version": "bedrock-2023-05-31"
            },
            provider="anthropic"
        )
        
        # Optimized RSS feed sources (fast and reliable)
        self.rss_feeds = {
            "Technology": [
                "https://feeds.feedburner.com/techcrunch/",
                "https://www.theverge.com/rss/index.xml",
                "https://feeds.arstechnica.com/arstechnica/index"
            ],
            "Artificial Intelligence": [
                "https://www.artificialintelligence-news.com/feed/",
                "https://venturebeat.com/ai/feed/",
                "https://feeds.feedburner.com/oreilly/radar"
            ],
            "Business": [
                "https://feeds.bloomberg.com/markets/news.rss",
                "https://feeds.reuters.com/reuters/businessNews",
                "https://www.cnbc.com/id/10001147/device/rss/rss.html"
            ],
            "Startups": [
                "https://feeds.feedburner.com/TechCrunch/startups",
                "https://www.entrepreneur.com/latest.rss",
                "https://feeds.venturebeat.com/VentureBeat/startup"
            ],
            "India Happenings": [
                "https://www.thehindu.com/news/national/feeder/default.rss",
                "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
                "https://economictimes.indiatimes.com/news/rssfeeds/1052732854.cms"
            ]
        }

    def fetch_rss_feed(self, url: str, timeout: int = 10) -> List[Dict]:
        """Fetch and parse RSS feed with timeout"""
        try:
            # Set user agent to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            articles = []
            for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                # Parse published date
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.now()
                except:
                    pub_date = datetime.now()
                
                # Only include recent articles (last 24 hours)
                if (datetime.now() - pub_date).days > 1:
                    continue
                
                articles.append({
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'published': pub_date,
                    'source': feed.feed.get('title', 'Unknown Source')
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return []

    def summarize_article_fast(self, title: str, content: str) -> str:
        """Fast article summarization with shorter prompts"""
        try:
            # Clean and truncate content
            clean_content = BeautifulSoup(content, 'html.parser').get_text()
            clean_content = clean_content[:800]  # Limit content length
            
            prompt = f"Summarize in 2 sentences: {title}\n\n{clean_content}"
            
            messages = [
                SystemMessage(content="Provide concise 2-sentence news summaries."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            return clean_content[:200] + "..." if len(clean_content) > 200 else clean_content

    def fetch_category_news_optimized(self, category: str, max_articles: int = 4) -> List[NewsItem]:
        """Fetch news for a category with optimized parallel processing"""
        news_items = []
        feeds = self.rss_feeds.get(category, [])
        
        # Fetch feeds in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            feed_futures = [
                executor.submit(self.fetch_rss_feed, feed_url, 8)  # 8 second timeout
                for feed_url in feeds
            ]
            
            all_articles = []
            for future in concurrent.futures.as_completed(feed_futures, timeout=15):
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Feed fetch failed: {e}")
            
            # Remove duplicates and sort by date
            unique_articles = {}
            for article in all_articles:
                title_key = article['title'][:50].lower()
                if title_key not in unique_articles:
                    unique_articles[title_key] = article
            
            sorted_articles = sorted(
                unique_articles.values(),
                key=lambda x: x['published'],
                reverse=True
            )[:max_articles]
            
            # Summarize in parallel
            summary_futures = [
                executor.submit(self.summarize_article_fast, article['title'], article['summary'])
                for article in sorted_articles
            ]
            
            for i, future in enumerate(concurrent.futures.as_completed(summary_futures, timeout=20)):
                try:
                    if i < len(sorted_articles):
                        article = sorted_articles[i]
                        summary = future.result()
                        
                        news_item = NewsItem(
                            title=article['title'],
                            summary=summary,
                            link=article['link'],
                            category=category,
                            published_date=article['published'],
                            source=article['source']
                        )
                        news_items.append(news_item)
                        
                except Exception as e:
                    logger.error(f"Error processing summary: {e}")
        
        return news_items

    def fetch_all_news_optimized(self) -> Dict[str, List[NewsItem]]:
        """Fetch news for all categories with maximum optimization"""
        start_time = datetime.now()
        logger.info("🚀 Starting optimized news fetch...")
        
        all_news = {}
        
        # Process all categories in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            category_futures = {
                category: executor.submit(self.fetch_category_news_optimized, category, 3)
                for category in self.rss_feeds.keys()
            }
            
            for category, future in category_futures.items():
                try:
                    news_items = future.result(timeout=45)  # 45 seconds per category
                    all_news[category] = news_items
                    logger.info(f"✅ {category}: {len(news_items)} articles")
                except concurrent.futures.TimeoutError:
                    logger.warning(f"⏰ Timeout for category: {category}")
                    all_news[category] = []
                except Exception as e:
                    logger.error(f"❌ Error fetching {category}: {e}")
                    all_news[category] = []
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        total_articles = sum(len(articles) for articles in all_news.values())
        
        logger.info(f"🎉 Optimized news fetch completed in {duration:.1f}s - {total_articles} articles")
        return all_news

def create_optimized_news_agent(aws_region: str = "us-east-1") -> OptimizedNewsAgent:
    """Factory function to create an optimized news agent"""
    return OptimizedNewsAgent(aws_region=aws_region)

# For backward compatibility
def create_fast_news_agent(aws_region: str = "us-east-1") -> OptimizedNewsAgent:
    """Factory function for backward compatibility"""
    return OptimizedNewsAgent(aws_region=aws_region)
