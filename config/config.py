import os
from dotenv import load_dotenv
from pathlib import Path

# 1. Define Base Directory (Root of your project)
BASE_DIR = Path(__file__).resolve().parent.parent

# Add BASE_DIR to sys.path so scripts can be run directly and still find absolute imports
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 2. Load the .env file explicitly from the root directory
load_dotenv(dotenv_path=BASE_DIR / ".env")

# --- Credentials ---
WORKDAY_EMAIL = os.getenv("WORKDAY_EMAIL")
WORKDAY_PASSWORD = os.getenv("WORKDAY_PASSWORD")
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# --- AI Models & Networking ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5:3b")

# --- Automation Settings ---
# Converts string "True"/"False" from .env into actual Python booleans
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "False").lower() in ("true", "1", "t")

# --- Standardized Paths ---
ASSETS_DIR = BASE_DIR / "assets"
RESUME_DIR = ASSETS_DIR / "resume"
PROFILES_DIR = ASSETS_DIR / "profiles"

# Ensure directories exist upon boot
RESUME_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)