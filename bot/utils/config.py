from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")
    GOOGLE_CX = os.getenv("GOOGLE_CX")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")