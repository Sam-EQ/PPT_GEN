import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in .env")

MARKER_LLM_MODEL = os.getenv("MARKER_LLM_MODEL", "gpt-4o-mini")

os.environ["TORCH_DEVICE"] = "cuda"
os.environ["IN_STREAMLIT"] = "true"
