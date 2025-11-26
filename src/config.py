import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Please create a .env file or set the environment variable."
    )

genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
MODEL = genai.GenerativeModel(MODEL_NAME)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "expense_manager.db"))
LOG_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
