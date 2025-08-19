import os
import json
import logging
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Compatibility fix for Python 3.13+
import sys
if sys.version_info >= (3, 13):
    # Create a mock cgi module for Python 3.13+
    import html
    class MockCGI:
        @staticmethod
        def escape(s, quote=False):
            return html.escape(s, quote=quote)
    
    sys.modules['cgi'] = MockCGI()

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

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

class FastNewsAgent:
    """Optimized news agent using DuckDuckGo search for faster results"""
    
    def __init__(self, aws_region: str = "us-east-1"):
        self.aws_region = aws_region
        
        # Initialize Claude 3.5 Sonnet via Bedrock with specific model ARN
        self.llm = ChatBedrock(
            model_id="arn:aws:bedrock:us-east-2:905418105552:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name="us-east-2",
            model_kwargs={
                "max_tokens": 1000,
                "temperature": 0.1,
                "anthropic_version": "bedrock-2023-05-31"
            },
            provider="anthropic"
        )
        
        # Search queries for each category (optimized for recent news)
        self.search_queries = {
            "Technology": [
                "latest technology news today",
                "tech startups 2025",
                "artificial intelligence breakthrough"
            ],
            "Artificial Intelligence": [
                "AI news today",
                "machine learning research",
                "ChatGPT OpenAI news"
            ],
            "Business": [
                "business news today",
                "stock market news",
                "corporate earnings"
            ],
            "Startups": [
                "startup funding news",
                "new tech startups",
                "venture capital investment"
            ],
            "India Happenings": [
                "India news today",
                "Indian government policy",
                "India technology sector"
            ]
        }

    def search_news_fast(self, query: str, max_results: int = 3) -> List[Dict]:
        """Fast news search using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = []
                news_results = ddgs.news(
                    keywords=query,
                    region='wt-wt',  # Worldwide
                    safesearch='moderate',
                    timelimit='d',  # Last day
                    max_results=max_results
                )
                
                for result in news_results:
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'snippet': result.get('body', ''),
                        'source': result.get('source', ''),
                        'date': result.get('date', datetime.now().isoformat())
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching news with DuckDuckGo: {e}")
            return []

    def summarize_content_fast(self, title: str, snippet: str, url: str) -> str:
        """Fast content summarization using Claude"""
        try:
            prompt = f"""
            Summarize this news article in 2-3 sentences. Focus on the key facts and impact:

            Title: {title}
            Content: {snippet}
            URL: {url}

            Provide a concise, informative summary that captures the main points.
            """

            messages = [
                SystemMessage(content="You are a news summarization expert. Provide clear, concise summaries."),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error summarizing content: {e}")
            return snippet[:200] + "..." if len(snippet) > 200 else snippet

    def fetch_category_news_parallel(self, category: str, max_articles: int = 3) -> List[NewsItem]:
        """Fetch news for a category using parallel processing"""
        news_items = []
        queries = self.search_queries.get(category, [f"{category} news today"])
        
        # Use ThreadPoolExecutor for parallel searches
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit search tasks
            search_futures = [
                executor.submit(self.search_news_fast, query, 2)
                for query in queries[:2]  # Limit to 2 queries per category for speed
            ]
            
            # Collect results
            all_results = []
            for future in concurrent.futures.as_completed(search_futures, timeout=10):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Search task failed: {e}")
            
            # Remove duplicates based on title similarity
            unique_results = []
            seen_titles = set()
            for result in all_results:
                title_key = result['title'].lower()[:50]  # First 50 chars for similarity check
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_results.append(result)
            
            # Limit results and process
            unique_results = unique_results[:max_articles]
            
            # Summarize content in parallel
            summary_futures = [
                executor.submit(
                    self.summarize_content_fast,
                    result['title'],
                    result['snippet'],
                    result['url']
                )
                for result in unique_results
            ]
            
            # Create NewsItem objects
            for i, future in enumerate(concurrent.futures.as_completed(summary_futures, timeout=15)):
                try:
                    if i < len(unique_results):
                        result = unique_results[i]
                        summary = future.result()
                        
                        # Parse date
                        try:
                            if isinstance(result['date'], str):
                                pub_date = datetime.fromisoformat(result['date'].replace('Z', '+00:00'))
                            else:
                                pub_date = datetime.now()
                        except:
                            pub_date = datetime.now()
                        
                        news_item = NewsItem(
                            title=result['title'],
                            summary=summary,
                            link=result['url'],
                            category=category,
                            published_date=pub_date,
                            source=result['source'] or 'DuckDuckGo News'
                        )
                        news_items.append(news_item)
                        
                except Exception as e:
                    logger.error(f"Error processing summary: {e}")
        
        return news_items

    def fetch_all_news_fast(self) -> Dict[str, List[NewsItem]]:
        """Fetch news for all categories with maximum parallelization"""
        start_time = datetime.now()
        logger.info("🚀 Starting fast news fetch with DuckDuckGo...")
        
        all_news = {}
        
        # Use ThreadPoolExecutor for category-level parallelization
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit tasks for all categories
            category_futures = {
                category: executor.submit(self.fetch_category_news_parallel, category, 3)
                for category in self.search_queries.keys()
            }
            
            # Collect results with timeout
            for category, future in category_futures.items():
                try:
                    news_items = future.result(timeout=30)  # 30 seconds per category
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
        
        logger.info(f"🎉 Fast news fetch completed in {duration:.1f}s - {total_articles} articles")
        return all_news

def create_fast_news_agent(aws_region: str = "us-east-1") -> FastNewsAgent:
    """Factory function to create a fast news agent"""
    return FastNewsAgent(aws_region=aws_region)

# Backward compatibility
def create_news_agent(aws_region: str = "us-east-1", tavily_api_key: str = None) -> FastNewsAgent:
    """Factory function for backward compatibility"""
    return FastNewsAgent(aws_region=aws_region)
