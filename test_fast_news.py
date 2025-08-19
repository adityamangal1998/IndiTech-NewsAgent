#!/usr/bin/env python3
"""
Test script for the fast news agent
"""

import os
import sys
from datetime import datetime

# Add Python 3.13 compatibility
if sys.version_info >= (3, 13):
    import html
    class MockCGI:
        @staticmethod
        def escape(s, quote=False):
            return html.escape(s, quote=quote)
    sys.modules['cgi'] = MockCGI()

from fast_news_agent import create_fast_news_agent

def test_fast_news():
    """Test the fast news agent"""
    print("🚀 Testing Fast News Agent...")
    
    start_time = datetime.now()
    
    # Create agent
    agent = create_fast_news_agent()
    
    # Test single category first
    print("\n📰 Testing single category (Technology)...")
    tech_news = agent.fetch_category_news_parallel("Technology", 2)
    
    print(f"✅ Found {len(tech_news)} tech articles:")
    for item in tech_news:
        print(f"  - {item.title[:80]}...")
    
    # Test all categories
    print("\n🌍 Testing all categories...")
    all_news = agent.fetch_all_news_fast()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n📊 Results:")
    total_articles = 0
    for category, articles in all_news.items():
        count = len(articles)
        total_articles += count
        print(f"  {category}: {count} articles")
    
    print(f"\n⏱️  Total time: {duration:.1f} seconds")
    print(f"📈 Total articles: {total_articles}")
    print(f"🚀 Speed: {total_articles/duration:.1f} articles/second")

if __name__ == "__main__":
    test_fast_news()
