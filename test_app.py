"""
Test script for Aditya Daily Digest
Simple tests to verify the application works correctly
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestNewsAgent(unittest.TestCase):
    """Test cases for the news agent"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'AWS_REGION': 'us-east-1',
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'TAVILY_API_KEY': 'test_tavily_key'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    @patch('news_agent.ChatBedrock')
    @patch('news_agent.TavilySearchResults')
    def test_news_agent_creation(self, mock_tavily, mock_bedrock):
        """Test that news agent can be created"""
        from news_agent import create_news_agent
        
        # Mock the LLM and search tool
        mock_bedrock.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()
        
        agent = create_news_agent()
        self.assertIsNotNone(agent)
        self.assertEqual(agent.aws_region, 'us-east-1')
    
    def test_categories_defined(self):
        """Test that news categories are properly defined"""
        from news_agent import NewsAgent
        
        # Create agent without initializing AWS/Tavily components
        with patch('news_agent.ChatBedrock'), patch('news_agent.TavilySearchResults'):
            agent = NewsAgent()
            
            expected_categories = [
                'Technology',
                'Artificial Intelligence', 
                'Business',
                'Startups',
                'India Happenings'
            ]
            
            for category in expected_categories:
                self.assertIn(category, agent.categories)
                self.assertIsInstance(agent.categories[category], list)
                self.assertGreater(len(agent.categories[category]), 0)
    
    def test_rss_feeds_defined(self):
        """Test that RSS feeds are properly defined"""
        from news_agent import NewsAgent
        
        with patch('news_agent.ChatBedrock'), patch('news_agent.TavilySearchResults'):
            agent = NewsAgent()
            
            # Check that RSS feeds are defined for each category
            for category in agent.categories.keys():
                self.assertIn(category, agent.rss_feeds)
                self.assertIsInstance(agent.rss_feeds[category], list)
                self.assertGreater(len(agent.rss_feeds[category]), 0)
                
                # Check that each feed URL is a string
                for feed_url in agent.rss_feeds[category]:
                    self.assertIsInstance(feed_url, str)
                    self.assertTrue(feed_url.startswith('http'))

class TestFlaskApp(unittest.TestCase):
    """Test cases for the Flask application"""
    
    def setUp(self):
        """Set up test Flask app"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'AWS_REGION': 'us-east-1',
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'TAVILY_API_KEY': 'test_tavily_key',
            'FLASK_ENV': 'testing'
        })
        self.env_patcher.start()
        
        # Mock the news agent initialization
        with patch('app.create_news_agent'):
            import app
            app.app.config['TESTING'] = True
            self.client = app.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
    
    def test_index_route(self):
        """Test that the index route responds"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Aditya Daily Digest', response.data)
    
    def test_health_route(self):
        """Test the health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_api_news_route(self):
        """Test the news API endpoint"""
        response = self.client.get('/api/news')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('news', data)
        self.assertIn('last_update', data)

class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_class(self):
        """Test configuration class"""
        from config import Config
        
        # Test default values
        self.assertEqual(Config.AWS_REGION, 'us-east-1')
        self.assertEqual(Config.NEWS_REFRESH_INTERVAL, 6)
        self.assertEqual(Config.MAX_NEWS_PER_CATEGORY, 5)
    
    @patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'test_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret',
        'TAVILY_API_KEY': 'test_tavily_key'
    })
    def test_config_validation_success(self):
        """Test configuration validation with valid config"""
        from config import Config
        
        # Should not raise an exception
        self.assertTrue(Config.validate_config())
    
    def test_config_validation_failure(self):
        """Test configuration validation with missing variables"""
        from config import Config
        
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as cm:
                Config.validate_config()
            
            self.assertIn('Missing required environment variables', str(cm.exception))

def run_basic_smoke_test():
    """Run a basic smoke test without full dependencies"""
    print("🧪 Running basic smoke test...")
    
    try:
        # Test imports
        import app
        import news_agent
        import config
        print("✅ All modules import successfully")
        
        # Test configuration
        from config import Config
        print(f"✅ Configuration loaded - AWS Region: {Config.AWS_REGION}")
        
        # Test Flask app creation
        flask_app = app.app
        print("✅ Flask app created successfully")
        
        print("🎉 Basic smoke test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        return False

if __name__ == '__main__':
    print("Aditya Daily Digest - Test Suite")
    print("=" * 40)
    
    # Run basic smoke test first
    if not run_basic_smoke_test():
        sys.exit(1)
    
    print("\n🔬 Running unit tests...")
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n✅ All tests completed!")
