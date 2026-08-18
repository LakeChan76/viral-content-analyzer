import os
from dotenv import load_dotenv

load_dotenv()

SENSENOVA_API_KEY = os.getenv("SENSENOVA_API_KEY", "")
SENSENOVA_BASE_URL = "https://api.sensenova.cn/v1"
LLM_MODEL = "deepseek-v4-flash"
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
APIFY_ACTOR_ID = "scrapesage~twitter-scraper"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
ASSET_LIBRARY_PATH = os.path.join(OUTPUT_DIR, "asset_library.json")

TOP_N = 5
ENGAGEMENT_RATE_BENCHMARK = 2.0
SIMILARITY_THRESHOLD = 0.7
