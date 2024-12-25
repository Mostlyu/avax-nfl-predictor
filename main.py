# api/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import engine
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import List, Dict
from predictor import NFLPredictor
from config import API_KEY
from contextlib import asynccontextmanager
from database import init_db, get_db
from weekly_manager import NFLWeeklyDataManager
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
weekly_manager = None
predictor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting application initialization...")
        init_db()
        logger.info("Database initialized successfully")

        global weekly_manager, predictor
        weekly_manager = NFLWeeklyDataManager(API_KEY)
        predictor = NFLPredictor(API_KEY)
        logger.info("Weekly manager and predictor initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        if weekly_manager:
            await weekly_manager.cleanup()

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"]  # Expose all headers
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "database": "connected",
            "weekly_manager": "initialized" if weekly_manager else "not initialized",
            "predictor": "initialized" if predictor else "not initialized",
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
    """Get upcoming NFL games schedule"""
    try:
        logger.info("Fetching NFL schedule...")
        weekly_manager.update_weekly_data()
        schedule_list = weekly_manager.get_cached_schedule()

        if not schedule_list:
            logger.warning("No games found")
            return {
                "success": True,
                "schedule": []
            }

        logger.info(f"Found {len(schedule_list)} upcoming games")
        return {
            "success": True,
            "schedule": schedule_list
        }

    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/predict/{game_id}")
async def get_prediction(game_id: int):
    try:
        logger.info(f"Getting prediction for game {game_id}")

        if not predictor:
            logger.error("Predictor not initialized")
            raise HTTPException(status_code=500, detail="Predictor not initialized")

        # Try to get the game directly
        response = requests.get(
            f"{predictor.base_url}/games",
            headers=predictor.headers,
            params={
                'id': str(game_id),
                'league': '1',
                'season': '2024'
            }
        )
        response.raise_for_status()
        game_data = response.json().get('response', [])

        if not game_data or len(game_data) == 0:
            raise HTTPException(status_code=404, detail="Game not found")

        game = game_data[0]
        home_team = game['teams']['home']['name']
        away_team = game['teams']['away']['name']
        game_date = game['game']['date']['date']

        logger.info(f"Found game: {home_team} vs {away_team} on {game_date}")

        # Get basic analysis
        analysis = predictor.analyze_matchup(home_team, away_team)
        if 'error' in analysis:
            raise HTTPException(status_code=500, detail=analysis['error'])

        # Calculate confidence scores
        confidence_scores = predictor.calculate_confidence_scores(analysis['advantages'])

        # Prepare final prediction
        prediction = {
            "success": True,
            "prediction": {
                "matchup": f"{home_team} (Home) vs {away_team} (Away)",
                "date": game_date,
                "statistical_analysis": {
                    "advantages": analysis['advantages']
                },
                "confidence_scores": confidence_scores,
                "betting_recommendations": []  # Simplified for now
            }
        }

        return prediction

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/db-test")
async def test_db():
    try:
        result = engine.execute("SELECT 1")
        return {"status": "Database connected successfully"}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}