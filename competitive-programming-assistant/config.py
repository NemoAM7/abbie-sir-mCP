import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Security & Credentials ---
TOKEN = os.environ.get("AUTH_TOKEN")
CLIST_API_KEY = os.environ.get("CLIST_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- User & Tool Configuration ---
MY_NUMBER = os.environ.get("MY_NUMBER")
DEFAULT_HANDLE = os.environ.get("DEFAULT_HANDLE", "")  # Optional - no default user handle

# --- Server & Client Configuration ---
SERVER_URL = "http://localhost:8086/mcp/"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8086

# --- Render Keep-Alive Configuration ---
# Set this to your deployed Render URL + health endpoint for keep-alive pings
# Example: "https://your-app-name.onrender.com/health"
RENDER_HEALTH_URL = os.environ.get("RENDER_HEALTH_URL", "")

# --- Assertions for Critical Variables ---
assert TOKEN, "FATAL: Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER, "FATAL: Please set MY_NUMBER in your .env file"
assert CLIST_API_KEY, "FATAL: Please set CLIST_API_KEY in your .env file"
assert GEMINI_API_KEY, "FATAL: Please set GEMINI_API_KEY in your .env file"