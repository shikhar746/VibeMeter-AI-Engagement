import os
from dotenv import load_dotenv

load_dotenv()

ENGAGEMENT_CSV_PATH = os.getenv("ENGAGEMENT_CSV_PATH", "data/engagement_results.csv")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "vibemeter")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HR_PASSWORD = os.getenv("HR_PASSWORD", "")
