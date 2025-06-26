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