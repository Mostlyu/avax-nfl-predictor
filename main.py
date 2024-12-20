# main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from contextlib import asynccontextmanager
from database import init_db, get_db, Base, engine
from weekly_manager import NFLWeeklyDataManager
from config import API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global weekly_manager instance
weekly_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database before application starts
    try:
        logger.info("Starting application initialization...")
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")

        # Initialize weekly manager after database is ready
        global weekly_manager
        logger.info("Initializing weekly manager...")
        weekly_manager = NFLWeeklyDataManager(API_KEY)
        logger.info("Weekly manager initialized successfully")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield

    # Cleanup
    if weekly_manager:
        await weekly_manager.cleanup()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        inspector = engine.inspect(engine)
        tables = inspector.get_table_names()

        return {
            "status": "healthy",
            "database_connected": True,
            "tables_present": tables,
            "weekly_manager": "initialized" if weekly_manager else "not initialized"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }