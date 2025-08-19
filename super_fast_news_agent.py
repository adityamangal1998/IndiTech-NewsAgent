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
    image_url: str = ""

class SuperFastNewsAgent:
    """Super fast news agent using RSS feeds without AI summarization"""
    
    def __init__(self, use_ai_summary: bool = False, aws_region: str = "us-east-1"):
        self.aws_region = aws_region
        self.use_ai_summary = use_ai_summary
        self.llm = None
        
        # Initialize Claude only if requested and credentials are available
        if use_ai_summary:
            try:
                from langchain_aws import ChatBedrock
                self.llm = ChatBedrock(
                    model_id="arn:aws:bedrock:us-east-2:905418105552:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
                    region_name="us-east-2",
                    model_kwargs={
                        "max_tokens": 400,
                        "temperature": 0.1,
                        "anthropic_version": "bedrock-2023-05-31"
                    },
                    provider="anthropic"
                )
            except Exception as e:
                logger.warning(f"AI summarization not available: {e}")
                self.use_ai_summary = False
        
        # Optimized RSS feed sources (fast and reliable)
        self.rss_feeds = {
            "Technology": [
                "https://feeds.feedburner.com/techcrunch/",
                "https://www.theverge.com/rss/index.xml",
                "https://feeds.arstechnica.com/arstechnica/index",
                "https://techcrunch.com/feed/"
            ],
            "Artificial Intelligence": [
                "https://www.artificialintelligence-news.com/feed/",
                "https://feeds.feedburner.com/venturebeat/SZYF"
            ],
            "Business": [
                "https://feeds.bloomberg.com/markets/news.rss",
                "https://www.cnbc.com/id/10001147/device/rss/rss.html",
                "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
                "https://feeds.reuters.com/reuters/businessNews"
            ],
            "Startups": [
                "https://feeds.feedburner.com/TechCrunch/startups",
                "https://feeds.feedburner.com/entrepreneur/latest"
            ],
            "India Happenings": [
                "https://www.thehindu.com/news/national/feeder/default.rss",
                "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
                "https://economictimes.indiatimes.com/news/rssfeeds/1052732854.cms",
                "https://feeds.feedburner.com/ndtvnews-latest"
            ],
            "Sports": [
                "https://rss.cnn.com/rss/edition_sport.rss",
                "https://feeds.bbci.co.uk/sport/rss.xml",
                "https://www.goal.com/feeds/en/news",
                "https://feeds.skysports.com/feeds/11095"
            ]
        }

    def fetch_rss_feed(self, url: str, timeout: int = 8) -> List[Dict]:
        """Fetch and parse RSS feed with timeout and enhanced headers"""
        try:
            # More comprehensive headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache'
            }
            
            # Try the request with retries for common errors
            max_retries = 2
            response = None
            
            for attempt in range(max_retries + 1):
                try:
                    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=True)
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403 and attempt < max_retries:
                        # Try with a different User-Agent on 403 error
                        headers['User-Agent'] = f'NewsBot/1.0 (+https://newsaggregator.com/bot)'
                        continue
                    elif e.response.status_code == 429 and attempt < max_retries:
                        # Rate limited, wait and retry
                        import time
                        time.sleep(2)
                        continue
                    else:
                        raise
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries:
                        # Try with different settings for SSL/connection errors
                        import time
                        time.sleep(1)
                        continue
                    else:
                        raise
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries:
                        continue
                    else:
                        raise
            
            if not response:
                return []
            
            # Parse the feed
            feed = feedparser.parse(response.content)
            
            # Check if the feed parsed successfully
            if hasattr(feed, 'bozo') and feed.bozo:
                # Try to determine if it's a critical parsing error
                if hasattr(feed, 'bozo_exception'):
                    exception_str = str(feed.bozo_exception)
                    if 'not well-formed' in exception_str.lower() or 'syntax error' in exception_str.lower():
                        logger.warning(f"Feed has serious parsing issues: {url} - {exception_str}")
                        return []
                    else:
                        logger.debug(f"Feed has minor parsing issues but proceeding: {url}")
                        
            # Check if we have any entries
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found in feed: {url}")
                return []
            
            articles = []
            for entry in feed.entries[:4]:  # Limit to 4 articles per feed
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.now()
                except:
                    pub_date = datetime.now()
                
                # Clean summary
                summary = entry.get('summary', '')
                if summary:
                    summary = BeautifulSoup(summary, 'html.parser').get_text()
                    summary = summary.strip()[:300] + "..." if len(summary) > 300 else summary
                else:
                    summary = "No summary available."
                
                # Extract image URL with better error handling
                image_url = ""
                try:
                    # Try media:content first (common in RSS feeds)
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url', '')
                    # Try enclosure
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        for enclosure in entry.enclosures:
                            if hasattr(enclosure, 'type') and enclosure.type and enclosure.type.startswith('image/'):
                                image_url = enclosure.href
                                break
                    # Try media:thumbnail
                    elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get('url', '')
                    # Try looking in content/description for img tags
                    elif entry.get('summary') or entry.get('description'):
                        content = entry.get('summary', '') or entry.get('description', '')
                        soup = BeautifulSoup(content, 'html.parser')
                        img_tag = soup.find('img')
                        if img_tag and img_tag.get('src'):
                            image_url = img_tag.get('src')
                    # Try links with media types
                    elif hasattr(entry, 'links'):
                        for link in entry.links:
                            if hasattr(link, 'type') and link.type and link.type.startswith('image/'):
                                image_url = link.href
                                break
                    # For TechCrunch feeds, try to extract from content
                    if not image_url and 'techcrunch' in url.lower():
                        if hasattr(entry, 'content') and entry.content:
                            content_text = entry.content[0].value if entry.content else ''
                            soup = BeautifulSoup(content_text, 'html.parser')
                            img_tag = soup.find('img')
                            if img_tag and img_tag.get('src'):
                                image_url = img_tag.get('src')
                except Exception as e:
                    logger.debug(f"Image extraction failed for {entry.get('title', 'Unknown')}: {e}")
                    pass  # If image extraction fails, continue without image
                
                # Validate basic required fields
                title = entry.get('title', 'No Title').strip()
                link = entry.get('link', '').strip()
                
                if not title or len(title) < 5:  # Skip entries with very short or missing titles
                    continue
                    
                articles.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'published': pub_date,
                    'source': feed.feed.get('title', 'RSS Feed'),
                    'image_url': image_url
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return []

    def summarize_with_ai(self, title: str, content: str) -> str:
        """AI-powered summarization if available"""
        if not self.use_ai_summary or not self.llm:
            return content[:250] + "..." if len(content) > 250 else content
        
        try:
            from langchain.schema import HumanMessage, SystemMessage
            
            prompt = f"Summarize this news in 2 clear sentences:\n\nTitle: {title}\nContent: {content[:500]}"
            
            messages = [
                SystemMessage(content="Provide clear, concise 2-sentence news summaries."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error with AI summarization: {e}")
            return content[:250] + "..." if len(content) > 250 else content

    def fetch_category_news_super_fast(self, category: str, max_articles: int = 3) -> List[NewsItem]:
        """Super fast news fetching for a category with improved error handling"""
        news_items = []
        feeds = self.rss_feeds.get(category, [])
        
        if not feeds:
            logger.warning(f"No RSS feeds configured for category: {category}")
            return news_items
        
        # Ensure we have at least 1 worker
        max_workers = max(1, min(len(feeds), 4))  # Cap at 4 workers to avoid overwhelming
        
        # Fetch feeds in parallel with shorter timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            feed_futures = [
                executor.submit(self.fetch_rss_feed, feed_url, 6)  # 6 second timeout
                for feed_url in feeds
            ]
            
            all_articles = []
            successful_feeds = 0
            for i, future in enumerate(concurrent.futures.as_completed(feed_futures, timeout=10)):
                try:
                    articles = future.result()
                    if articles:  # Only count if we got articles
                        all_articles.extend(articles)
                        successful_feeds += 1
                        logger.info(f"✅ {category} feed {i+1}: {len(articles)} articles")
                    else:
                        logger.warning(f"⚠️ {category} feed {i+1}: No articles returned")
                except Exception as e:
                    logger.error(f"❌ {category} feed {i+1} failed: {e}")
            
            # Log summary for the category
            logger.info(f"📊 {category}: {successful_feeds}/{len(feeds)} feeds successful, {len(all_articles)} total articles")
            
            # Remove duplicates and get latest
            unique_articles = {}
            for article in all_articles:
                title_key = article['title'][:40].lower()
                if title_key not in unique_articles:
                    unique_articles[title_key] = article
            
            sorted_articles = sorted(
                unique_articles.values(),
                key=lambda x: x['published'],
                reverse=True
            )[:max_articles]
            
            # Process articles (with optional AI summarization)
            for article in sorted_articles:
                summary = self.summarize_with_ai(article['title'], article['summary'])
                
                news_item = NewsItem(
                    title=article['title'],
                    summary=summary,
                    link=article['link'],
                    category=category,
                    published_date=article['published'],
                    source=article['source'],
                    image_url=article.get('image_url', '')
                )
                news_items.append(news_item)
        
        return news_items

    def fetch_all_news_super_fast(self) -> Dict[str, List[NewsItem]]:
        """Super fast news fetch for all categories"""
        start_time = datetime.now()
        logger.info("🚀 Starting super fast news fetch...")
        
        all_news = {}
        
        # Process all categories in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            category_futures = {
                category: executor.submit(self.fetch_category_news_super_fast, category, 3)
                for category in self.rss_feeds.keys()
            }
            
            for category, future in category_futures.items():
                try:
                    news_items = future.result(timeout=20)  # 20 seconds per category
                    all_news[category] = news_items
                    logger.info(f"✅ {category}: {len(news_items)} articles")
                except Exception as e:
                    logger.error(f"❌ {category}: {e}")
                    all_news[category] = []
        
        end_time = datetime.now()
        total_articles = sum(len(items) for items in all_news.values())
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"🎉 Super fast news fetch completed in {duration:.1f}s - {total_articles} articles")
        return all_news
    
    def fetch_category_news_extended(self, category: str, max_articles: int = 10) -> List[NewsItem]:
        """Fetch more articles for a specific category (for category pages)"""
        return self.fetch_category_news_super_fast(category, max_articles)

def create_super_fast_news_agent(use_ai_summary: bool = True, aws_region: str = "us-east-1") -> SuperFastNewsAgent:
    """Factory function to create a super fast news agent"""
    return SuperFastNewsAgent(use_ai_summary=use_ai_summary, aws_region=aws_region)

# For backward compatibility
def create_optimized_news_agent(aws_region: str = "us-east-1") -> SuperFastNewsAgent:
    """Factory function for backward compatibility"""
    return SuperFastNewsAgent(use_ai_summary=True, aws_region=aws_region)
