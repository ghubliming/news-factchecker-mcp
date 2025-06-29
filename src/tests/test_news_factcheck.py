import pytest
import asyncio
from src.factcheck.news_factcheck import NewsFactChecker
from dotenv import load_dotenv
from os import getenv
import os
import datetime

load_dotenv()

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, 'test_news_factcheck.log')

def log_result(message):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n--- {timestamp} ---\n")
        f.write(message + '\n')

gemini_api_key = getenv('GEMINI_API_KEY')
news_api_key = getenv('NEWS_API_KEY')

@pytest.mark.asyncio
async def test_news_api_trending_topics():
    """Test News API functionality for getting trending topics"""
    if not gemini_api_key:
        pytest.skip('GEMINI_API_KEY not set in environment or .env file')
    
    # Initialize fact checker with optional News API key
    fact_checker = NewsFactChecker(gemini_api_key, news_api_key=news_api_key)
    
    # Test international trending topics
    location = "international"
    result = await fact_checker.get_trending_topics(location)
    
    log_result(f"Tested News API trending topics for location: {location}\nNumber of topics returned: {len(result)}\nTopics: {result}\n")
    
    # Verify the response structure
    assert isinstance(result, list), "Result should be a list"
    
    if result:  # If we got results, verify their structure
        for topic in result:
            assert isinstance(topic, dict), "Each topic should be a dictionary"
            assert 'title' in topic, "Each topic should have a title"
            assert 'source' in topic, "Each topic should have a source"
            assert 'category' in topic, "Each topic should have a category"
            
    # Test local/Indian trending topics
    location = "local"
    result_local = await fact_checker.get_trending_topics(location)
    
    log_result(f"Tested News API trending topics for location: {location}\nNumber of topics returned: {len(result_local)}\nTopics: {result_local}\n")
    
    assert isinstance(result_local, list), "Local result should be a list"

@pytest.mark.asyncio
async def test_fact_check_headline():
    if not gemini_api_key:
        pytest.skip('GEMINI_API_KEY not set in environment or .env file')
    fact_checker = NewsFactChecker(gemini_api_key)
    headline = "NASA announces discovery of aliens on Mars"
    #headline = "Munich Terrorist Attack: 10 Dead, June, 2025"
    #headline = "Munich is safest city in Germany 2025"
    result = await fact_checker.fact_check_headline(headline)
    log_result(f"Tested headline: {headline}\nResult: {result}\n")
    assert 'verdict' in result
    assert 'confidence' in result
    assert 'truthfulness_percentage' in result

@pytest.mark.asyncio
async def test_news_api_comprehensive():
    """Comprehensive test for News API functionality with detailed validations"""
    if not gemini_api_key:
        pytest.skip('GEMINI_API_KEY not set in environment or .env file')
    
    fact_checker = NewsFactChecker(gemini_api_key, news_api_key=news_api_key)
    
    # Test both international and local
    locations = ["international", "local"]
    
    for location in locations:
        result = await fact_checker.get_trending_topics(location)
        
        log_result(f"Comprehensive test for location: {location}\nNumber of topics: {len(result)}")
        
        # Basic structure tests
        assert isinstance(result, list), f"Result for {location} should be a list"
        assert len(result) > 0, f"Should get at least some topics for {location}"
        
        # Detailed validation of each topic
        for i, topic in enumerate(result):
            assert isinstance(topic, dict), f"Topic {i} should be a dictionary"
            
            # Required fields
            required_fields = ['title', 'source', 'category']
            for field in required_fields:
                assert field in topic, f"Topic {i} missing required field: {field}"
                assert topic[field], f"Topic {i} has empty {field}"
            
            # Optional but expected fields
            expected_fields = ['description', 'url', 'published_at']
            for field in expected_fields:
                if field in topic:
                    assert topic[field], f"Topic {i} has empty {field}"
            
            # Data type validations
            assert isinstance(topic['title'], str), f"Title should be string in topic {i}"
            assert len(topic['title']) > 0, f"Title should not be empty in topic {i}"
            
            if 'url' in topic:
                assert topic['url'].startswith(('http://', 'https://', '<![CDATA[')), f"Invalid URL format in topic {i}"
        
        log_result(f"All validations passed for {location} - {len(result)} topics validated\n")