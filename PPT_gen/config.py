import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DEBUG_DIR = Path("tmp/deck_runs")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in .env")

OPENAI_MODEL_SUMMARY = os.getenv("OPENAI_MODEL_SUMMARY", "gpt-4o")
OPENAI_MODEL_SLIDES  = os.getenv("OPENAI_MODEL_SLIDES",  "gpt-4o")

MAX_SLIDES            = int(os.getenv("MAX_SLIDES", 20))
MIN_BULLETS_PER_SLIDE = int(os.getenv("MIN_BULLETS_PER_SLIDE", 3))
DEFAULT_THEME         = os.getenv("DEFAULT_THEME", "minimal")
SAVE_DEBUG_ARTIFACTS  = os.getenv("SAVE_DEBUG_ARTIFACTS", "true").lower() == "true"
ENABLE_HTML_PREVIEW   = os.getenv("ENABLE_HTML_PREVIEW", "false").lower() == "true"
LOG_LEVEL             = os.getenv("LOG_LEVEL", "INFO")