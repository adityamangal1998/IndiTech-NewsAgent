#!/usr/bin/env python3
"""
Setup script for Aditya Daily Digest
Helps configure the application and check dependencies
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version}")
        return True

def check_virtual_environment():
    """Check if running in virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  Not running in virtual environment (recommended)")
        return False

def install_requirements():
    """Install required packages"""
    try:
        print("📦 Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        create_env = input("Would you like to create a template .env file? (y/n): ")
        if create_env.lower() == 'y':
            create_env_template()
        return False
    
    # Read and check for required variables
    required_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "TAVILY_API_KEY"
    ]
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=your_" in content or f"{var}=" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing or template values in .env: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ .env file configured")
        return True

def create_env_template():
    """Create a template .env file"""
    template = """# AWS Credentials (Required)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Tavily Search API Key (Required)
TAVILY_API_KEY=your_tavily_api_key_here

# News API Key (Optional - for additional news sources)
NEWS_API_KEY=your_news_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production

# News Refresh Schedule (in hours)
NEWS_REFRESH_INTERVAL=6
MAX_NEWS_PER_CATEGORY=5
"""
    
    with open(".env", "w") as f:
        f.write(template)
    
    print("✅ Template .env file created")
    print("📝 Please edit .env file with your actual credentials")

def test_aws_credentials():
    """Test AWS credentials and Bedrock access"""
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        session = boto3.Session(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Test STS to verify credentials
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials valid - Account: {identity.get('Account')}")
        
        # Test Bedrock access
        bedrock = session.client('bedrock')
        models = bedrock.list_foundation_models()
        
        # Check if Claude 3.5 Sonnet is available
        claude_models = [m for m in models['modelSummaries'] if 'claude-3-5-sonnet' in m['modelId']]
        if claude_models:
            print("✅ AWS Bedrock access confirmed - Claude 3.5 Sonnet available")
            return True
        else:
            print("⚠️  Claude 3.5 Sonnet not found in available models")
            print("   Available Claude models:")
            for model in models['modelSummaries']:
                if 'claude' in model['modelId']:
                    print(f"   - {model['modelId']}")
            return False
            
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid")
        return False
    except ClientError as e:
        print(f"❌ AWS error: {e}")
        return False
    except ImportError:
        print("⚠️  boto3 not installed - skipping AWS test")
        return False

def test_tavily_api():
    """Test Tavily API key"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key or api_key.startswith('your_'):
            print("❌ Tavily API key not configured")
            return False
        
        # Simple test request
        import requests
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": "test",
                "max_results": 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Tavily API key valid")
            return True
        else:
            print(f"❌ Tavily API error: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  requests not installed - skipping Tavily test")
        return False
    except Exception as e:
        print(f"❌ Tavily test failed: {e}")
        return False

def run_quick_test():
    """Run a quick test of the news agent"""
    try:
        print("🧪 Running quick news agent test...")
        
        # Import and test news agent
        from news_agent import create_news_agent
        
        agent = create_news_agent()
        
        # Try to fetch a small amount of news
        test_news = agent.fetch_rss_news("Technology", limit=2)
        
        if test_news:
            print(f"✅ News agent test passed - fetched {len(test_news)} articles")
            return True
        else:
            print("⚠️  News agent test: no articles fetched")
            return False
            
    except Exception as e:
        print(f"❌ News agent test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Aditya Daily Digest Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check virtual environment
    check_virtual_environment()
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Check .env file
    env_configured = check_env_file()
    
    if env_configured:
        # Test AWS credentials
        aws_ok = test_aws_credentials()
        
        # Test Tavily API
        tavily_ok = test_tavily_api()
        
        if aws_ok and tavily_ok:
            # Run quick test
            test_ok = run_quick_test()
            
            if test_ok:
                print("\n🎉 Setup completed successfully!")
                print("Run 'python app.py' to start the application")
                return True
    
    print("\n⚠️  Setup completed with issues")
    print("Please resolve the above issues before running the application")
    print("\nNext steps:")
    print("1. Configure your .env file with valid credentials")
    print("2. Run this setup script again to verify")
    print("3. Start the application with 'python app.py'")
    
    return False

if __name__ == "__main__":
    main()
