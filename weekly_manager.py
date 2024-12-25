import logging
from datetime import datetime, timedelta
import requests
from database import SessionLocal, TeamMapping
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NFLWeeklyDataManager:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://v1.american-football.api-sports.io"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "v1.american-football.api-sports.io"
        }
        self.cached_schedule = None
        self.last_update = None
        logger.info("NFLWeeklyDataManager initialized")

    async def cleanup(self):
        logger.info("Cleaning up NFLWeeklyDataManager")

    def fetch_games_for_date(self, date_str):
        """Fetch games for a specific date"""
        try:
            response = requests.get(
                f"{self.base_url}/games",
                headers=self.headers,
                params={
                    "league": "1",
                    "season": "2024",
                    "date": date_str
                }
            )
            response.raise_for_status()
            return response.json().get("response", [])
        except Exception as e:
            logger.error(f"Error fetching games for date {date_str}: {e}")
            return []

    def update_weekly_data(self):
        """Update weekly data if needed"""
        current_time = datetime.now()

        if (not self.cached_schedule or
            not self.last_update or
            (current_time - self.last_update) > timedelta(hours=6)):

            try:
                formatted_games = []
                # Fetch games for the next 7 days
                for i in range(7):
                    date = current_time + timedelta(days=i)
                    date_str = date.strftime('%Y-%m-%d')
                    logger.info(f"Fetching games for date: {date_str}")

                    games = self.fetch_games_for_date(date_str)

                    for game in games:
                        try:
                            game_info = game["game"]
                            teams = game["teams"]
                            venue = game_info["venue"]
                            date_info = game_info["date"]
                            status = game_info["status"]

                            formatted_game = {
                                "id": game_info["id"],
                                "date": date_info["date"],
                                "time": date_info["time"],
                                "home_team": teams["home"]["name"],
                                "away_team": teams["away"]["name"],
                                "stadium": venue["name"],
                                "city": venue["city"],
                                "status": status["long"]
                            }
                            formatted_games.append(formatted_game)
                            logger.info(f"Processed game: {formatted_game}")
                        except Exception as e:
                            logger.error(f"Error formatting game: {e}")
                            continue

                self.cached_schedule = formatted_games
                self.last_update = current_time
                logger.info(f"Updated schedule cache with {len(formatted_games)} games")

            except Exception as e:
                logger.error(f"Error updating weekly data: {e}")
                if not self.cached_schedule:
                    self.cached_schedule = []
                raise

    def get_cached_schedule(self):
        """Get the cached schedule"""
        if not self.cached_schedule:
            self.update_weekly_data()
        return self.cached_schedule