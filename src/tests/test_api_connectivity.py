import os
import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, 'test_api_connectivity.log')

def log_result(message):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n--- {timestamp} ---\n")
        f.write(message + '\n')

def test_gemini_api():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        msg = 'GEMINI_API_KEY not set in environment or .env file.'
        print(msg)
        log_result(msg)
        return False
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Say hello")
        msg = f"Gemini API connectivity: SUCCESS. Model response: {response.text.strip()}"
        print(msg)
        log_result(msg)
        return True
    except Exception as e:
        msg = f"Gemini API connectivity: ERROR. Exception: {e}"
        print(msg)
        log_result(msg)
        return False

if __name__ == '__main__':
    test_gemini_api() 