# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    WEATHER_API = os.getenv("WEATHER_API")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    EXCHANGE_RATE_API = os.getenv("EXCHANGE_RATE_API")

    @staticmethod
    def set_environment():
        """Set environment variables for APIs."""
        os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY
        os.environ["TAVILY_API_KEY"] = Config.TAVILY_API_KEY
        os.environ["SERPER_API_KEY"] = Config.SERPER_API_KEY