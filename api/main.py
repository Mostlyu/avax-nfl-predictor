# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from predictor import NFLPredictor
from config import API_KEY
from weekly_manager import NFLWeeklyDataManager
import logging
import requests

# Initialize weekly data manager (after your other initializations)
weekly_manager = NFLWeeklyDataManager(API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor
predictor = NFLPredictor(API_KEY)

@app.get("/schedule")
async def get_schedule():
    """Get upcoming NFL games schedule"""
    try:
        logger.info("Fetching NFL schedule...")

        # Only updates if more than 7 days have passed
        weekly_manager.update_weekly_data()

        # Get schedule from cache
        schedule_list = weekly_manager.get_cached_schedule()

        logger.info(f"Found {len(schedule_list)} upcoming games")

        return {
            "success": True,
            "schedule": schedule_list
        }

    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.get("/predict/{game_id}")
async def get_prediction(game_id: int):
    try:
        logger.info(f"Getting prediction for game {game_id}")

        # Check cache first
        cached_prediction = predictor.get_cached_prediction(game_id)
        if cached_prediction:
            logger.info("Using cached prediction")
            return cached_prediction

        # Try to get the game directly first
        try:
            # Try cache for game data first
            cached_game = predictor.get_cached_game_data(game_id)
            if cached_game:
                game = cached_game
                logger.info("Using cached game data")
            else:
                direct_response = requests.get(
                    f"{predictor.base_url}/games",
                    headers=predictor.headers,
                    params={
                        'id': str(game_id),
                        'league': '1',
                        'season': '2024'
                    }
                )
                direct_response.raise_for_status()
                game_data = direct_response.json().get('response', [])

                if game_data and len(game_data) > 0:
                    game = game_data[0]
                else:
                    # If direct lookup fails, try date range search
                    for i in range(7):
                        date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                        response = requests.get(
                            f"{predictor.base_url}/games",
                            headers=predictor.headers,
                            params={
                                'league': '1',
                                'season': '2024',
                                'date': date
                            }
                        )
                        response.raise_for_status()
                        games = response.json().get('response', [])

                        game = next((g for g in games if g['game']['id'] == game_id), None)
                        if game:
                            # Cache game data when found
                            predictor.cache_game_data(game_id, game)
                            break

                    if not game:
                        raise HTTPException(status_code=404, detail="Game not found")

            # Process the found game
            home_team = game['teams']['home']['name']
            away_team = game['teams']['away']['name']
            game_date = game['game']['date']['date']

            logger.info(f"Found game: {home_team} vs {away_team} on {game_date}")

            # Get basic analysis
            analysis = predictor.analyze_matchup(home_team, away_team)
            if 'error' in analysis:
                raise HTTPException(status_code=500, detail=analysis['error'])

            # Add required info for best_odds
            analysis['home_team'] = home_team
            analysis['away_team'] = away_team
            analysis['game_date'] = game_date

            # Calculate confidence scores
            confidence_scores = predictor.calculate_confidence_scores(analysis['advantages'])
            analysis['confidence_scores'] = confidence_scores

            # Get odds
            odds = predictor.get_game_odds(game_id)
            recommendations = predictor.find_best_odds(analysis, odds)

            # Log analysis details
            logger.info(f"Analysis advantages: {analysis['advantages']}")
            logger.info(f"Base confidence scores: {confidence_scores}")
            logger.info(f"Final recommendations: {recommendations}")

            # Prepare final prediction
            prediction = {
                "success": True,
                "prediction": {
                    "matchup": f"{home_team} (Home) vs {away_team} (Away)",
                    "date": game_date,
                    "statistical_analysis": {
                        "advantages": analysis['advantages']
                    },
                    "betting_recommendations": recommendations or []
                }
            }

            # Cache the complete prediction
            predictor.cache_prediction_data(game_id, prediction)

            return prediction

        except requests.RequestException as e:
            logger.error(f"API request error: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch game data")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }