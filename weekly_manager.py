import logging
from datetime import datetime, timedelta
import requests
from database import SessionLocal, TeamMapping, WeeklySchedule, APICallTracker
from sqlalchemy import and_
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def track_api_call(db, endpoint: str):
    """Track API call and check daily limit"""
    today = datetime.now().strftime('%Y-%m-%d')

    # Count today's calls
    daily_calls = db.query(APICallTracker).filter(
        APICallTracker.date == today
    ).count()

    if daily_calls >= 7000:  # Leave buffer for emergency
        logger.warning(f"API call limit approaching: {daily_calls} calls today")

    # Record the call
    db.add(APICallTracker(endpoint=endpoint, date=today))
    db.commit()

    return daily_calls

class NFLWeeklyDataManager:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://v1.american-football.api-sports.io"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "v1.american-football.api-sports.io"
        }
        self.db = SessionLocal()
        logger.info("NFLWeeklyDataManager initialized")

    async def cleanup(self):
        logger.info("Cleaning up NFLWeeklyDataManager")
        self.db.close()

    def update_weekly_data(self):
        """Update weekly data if needed"""
        try:
            # Check if we have valid cached data
            now = datetime.now()
            cached_schedule = self.db.query(WeeklySchedule).filter(
                WeeklySchedule.cache_valid_until > now
            ).all()

            if cached_schedule:
                logger.info("Using cached schedule data")
                return

            # Track API call
            daily_calls = track_api_call(self.db, "games")
            if daily_calls >= 7000:
                logger.warning("API call limit reached, using cached data")
                return

            logger.info(f"Fetching NFL games for season {datetime.now().year}")

            # Fetch next 7 days in a single API call
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

            response = requests.get(
                f"{self.base_url}/games",
                headers=self.headers,
                params={
                    'league': '1',
                    'season': '2024',
                    'from': start_date,
                    'to': end_date
                }
            )

            response.raise_for_status()
            games_data = response.json()

            # Clear old schedule data
            self.db.query(WeeklySchedule).delete()

            if games_data.get("response"):
                for game in games_data["response"]:
                    try:
                        game_info = {
                            "id": game["game"]["id"],
                            "date": game["game"]["date"]["date"],
                            "time": game["game"]["date"]["time"],
                            "home_team": game["teams"]["home"]["name"],
                            "away_team": game["teams"]["away"]["name"],
                            "stadium": game["game"]["venue"]["name"],
                            "city": game["game"]["venue"]["city"],
                            "status": game["game"]["status"]["long"],
                            "cache_valid_until": now + timedelta(hours=1)
                        }

                        self.db.add(WeeklySchedule(**game_info))
                        logger.info(f"Processed game: {game_info}")

                    except Exception as e:
                        logger.error(f"Error processing game: {e}")
                        continue

                self.db.commit()
                logger.info("Schedule cache updated successfully")

        except Exception as e:
            logger.error(f"Error updating weekly data: {e}")
            self.db.rollback()
            raise

    def get_cached_schedule(self):
        """Get cached schedule"""
        try:
            schedule = self.db.query(WeeklySchedule).all()
            return [
                {
                    "id": game.id,
                    "date": game.date,
                    "time": game.time,
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "stadium": game.stadium,
                    "city": game.city,
                    "status": game.status
                }
                for game in schedule
            ]
        except Exception as e:
            logger.error(f"Error getting cached schedule: {e}")
            return []