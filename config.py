import os
from dotenv import load_dotenv

load_dotenv('production.env')

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set")