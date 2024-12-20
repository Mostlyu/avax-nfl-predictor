from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database_manager import init_db
from weekly_manager import NFLWeeklyDataManager
from config import API_KEY

app = FastAPI()

# Initialize database
init_db()

# Initialize weekly manager
weekly_manager = NFLWeeklyDataManager(API_KEY)