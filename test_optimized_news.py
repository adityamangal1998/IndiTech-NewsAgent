#!/usr/bin/env python3
"""
Test script for the optimized news agent
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

from optimized_news_agent import create_optimized_news_agent

def test_optimized_news():
    """Test the optimized news agent"""
    print("🚀 Testing Optimized News Agent...")
    
    start_time = datetime.now()
    
    # Create agent
    agent = create_optimized_news_agent()
    
    # Test single category first
    print("\n📰 Testing single category (Technology)...")
    tech_news = agent.fetch_category_news_optimized("Technology", 2)
    
    print(f"✅ Found {len(tech_news)} tech articles:")
    for item in tech_news:
        print(f"  - {item.title[:80]}...")
        print(f"    Summary: {item.summary[:100]}...")
        print(f"    Source: {item.source}")
        print()
    
    # Test all categories
    print("\n🌍 Testing all categories...")
    all_news = agent.fetch_all_news_optimized()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n📊 Results:")
    total_articles = 0
    for category, articles in all_news.items():
        count = len(articles)
        total_articles += count
        print(f"  {category}: {count} articles")
        if articles:
            print(f"    Latest: {articles[0].title[:60]}...")
    
    print(f"\n⏱️  Total time: {duration:.1f} seconds")
    print(f"📈 Total articles: {total_articles}")
    if duration > 0:
        print(f"🚀 Speed: {total_articles/duration:.1f} articles/second")

if __name__ == "__main__":
    test_optimized_news()
