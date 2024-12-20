# main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import os
from contextlib import asynccontextmanager
from database import init_db, get_db, Base, engine
from weekly_manager import NFLWeeklyDataManager
from config import API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global weekly_manager instance
weekly_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application initialization...")

    # Log environment variables (excluding sensitive data)
    logger.info(f"API_KEY present: {'Yes' if API_KEY else 'No'}")
    logger.info(f"DATABASE_URL present: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")

    try:
        # Initialize database first
        logger.info("Starting database initialization...")
        init_db()
        logger.info("Database initialization completed")

        # Initialize weekly manager
        logger.info("Starting weekly manager initialization...")
        global weekly_manager
        weekly_manager = NFLWeeklyDataManager(API_KEY)
        logger.info("Weekly manager initialization completed")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        logger.error(f"Error type: {type(e)}")
        raise

    logger.info("Application initialization completed successfully")
    yield

    logger.info("Shutting down application...")
    if weekly_manager:
        await weekly_manager.cleanup()
    logger.info("Shutdown complete")

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
        # Test database connection
        result = db.execute("SELECT 1").scalar()

        # Get table names
        inspector = engine.inspect(engine)
        tables = inspector.get_table_names()

        return {
            "status": "healthy",
            "database_connected": True,
            "tables_present": tables,
            "weekly_manager_status": "initialized" if weekly_manager else "not initialized",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }