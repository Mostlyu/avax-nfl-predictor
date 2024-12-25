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

    def update_weekly_data(self):
        """Update weekly data if needed"""
        current_time = datetime.now()

        # Only update if cache is empty or older than 6 hours
        if (not self.cached_schedule or
            not self.last_update or
            (current_time - self.last_update) > timedelta(hours=6)):

            try:
                current_year = datetime.now().year
                season = current_year if datetime.now().month > 6 else current_year - 1

                logger.info(f"Fetching NFL games for season {season}")

                # Fetch games for next 7 days
                formatted_games = []
                for i in range(7):
                    date = current_time + timedelta(days=i)
                    date_str = date.strftime('%Y-%m-%d')

                    response = requests.get(
                        f"{self.base_url}/games",
                        headers=self.headers,
                        params={
                            "league": "1",
                            "season": str(season),
                            "date": date_str
                        }
                    )
                    response.raise_for_status()
                    games_data = response.json()

                    if games_data.get("response"):
                        for game in games_data["response"]:
                            try:
                                # Access the nested structure correctly
                                formatted_game = {
                                    "id": game["game"]["id"],
                                    "date": game["game"]["date"]["date"],
                                    "time": game["game"]["date"]["time"],
                                    "home_team": game["teams"]["home"]["name"],
                                    "away_team": game["teams"]["away"]["name"],
                                    "stadium": game["game"]["venue"]["name"],
                                    "city": game["game"]["venue"]["city"],
                                    "status": game["game"]["status"]["long"]
                                }
                                formatted_games.append(formatted_game)
                                logger.info(f"Processed game: {formatted_game}")
                            except (KeyError, TypeError) as e:
                                logger.error(f"Error processing game: {e}")
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