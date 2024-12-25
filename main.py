from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from database import init_db, get_db
from weekly_manager import NFLWeeklyDataManager
from config import API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global weekly_manager instance
weekly_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting application initialization...")
        init_db()
        logger.info("Database initialized successfully")

        global weekly_manager
        weekly_manager = NFLWeeklyDataManager(API_KEY)
        logger.info("Weekly manager initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        if weekly_manager:
            await weekly_manager.cleanup()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware with all origins allowed for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    try:
        return {
            "status": "healthy",
            "database": "connected",
            "weekly_manager": "initialized" if weekly_manager else "not initialized",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/schedule")
async def get_schedule():
    try:
        # For testing, return mock data
        mock_schedule = [
            {
                "id": 1,
                "date": "2024-12-24",
                "time": "20:00",
                "home_team": "Kansas City Chiefs",
                "away_team": "Las Vegas Raiders",
                "stadium": "Arrowhead Stadium",
                "city": "Kansas City",
                "status": "Not Started"
            },
            {
                "id": 2,
                "date": "2024-12-25",
                "time": "16:30",
                "home_team": "San Francisco 49ers",
                "away_team": "Baltimore Ravens",
                "stadium": "Levi's Stadium",
                "city": "Santa Clara",
                "status": "Not Started"
            }
        ]
        return {"success": True, "schedule": mock_schedule}
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        return {"success": False, "error": str(e)}