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

        if (not self.cached_schedule or
            not self.last_update or
            (current_time - self.last_update) > timedelta(hours=6)):

            try:
                # Get current NFL season
                current_year = datetime.now().year
                season = current_year if datetime.now().month > 6 else current_year - 1

                logger.info(f"Fetching NFL games for season {season}")

                response = requests.get(
                    f"{self.base_url}/games",
                    headers=self.headers,
                    params={
                        "league": "1",
                        "season": str(season),
                        "date": datetime.now().strftime('%Y-%m-%d')
                    }
                )

                # Log raw response for debugging
                logger.info(f"API Response Status: {response.status_code}")
                logger.info(f"API Response Headers: {response.headers}")
                logger.info(f"API Response Content: {response.text[:500]}...")  # First 500 chars

                response.raise_for_status()
                games_data = response.json()

                logger.info(f"Parsed JSON data: {games_data.keys()}")

                if games_data.get("response"):
                    formatted_games = []
                    for game in games_data["response"]:
                        logger.info(f"Processing game: {game}")  # Log each game object
                        try:
                            formatted_game = {
                                "id": game.get("id"),
                                "date": game.get("date", {}).get("date"),
                                "time": game.get("date", {}).get("time"),
                                "home_team": game.get("teams", {}).get("home", {}).get("name"),
                                "away_team": game.get("teams", {}).get("away", {}).get("name"),
                                "stadium": game.get("venue", {}).get("name"),
                                "city": game.get("venue", {}).get("city"),
                                "status": game.get("status", {}).get("long", "Not Started")
                            }
                            logger.info(f"Formatted game: {formatted_game}")
                            formatted_games.append(formatted_game)
                        except Exception as e:
                            logger.error(f"Error formatting game: {e}")
                            continue

                    self.cached_schedule = formatted_games
                    self.last_update = current_time
                    logger.info(f"Updated schedule cache with {len(formatted_games)} games")
                else:
                    # If no games found, use mock data for testing
                    logger.warning("No games found, using mock data")
                    self.cached_schedule = [
                        {
                            "id": 1,
                            "date": "2024-12-25",
                            "time": "16:30",
                            "home_team": "San Francisco 49ers",
                            "away_team": "Baltimore Ravens",
                            "stadium": "Levi's Stadium",
                            "city": "Santa Clara",
                            "status": "Not Started"
                        },
                        {
                            "id": 2,
                            "date": "2024-12-25",
                            "time": "20:00",
                            "home_team": "Kansas City Chiefs",
                            "away_team": "Las Vegas Raiders",
                            "stadium": "Arrowhead Stadium",
                            "city": "Kansas City",
                            "status": "Not Started"
                        }
                    ]

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching NFL data: {str(e)}")
                if not self.cached_schedule:
                    self.cached_schedule = []
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if not self.cached_schedule:
                    self.cached_schedule = []
                raise

    def get_cached_schedule(self):
        """Get the cached schedule"""
        if not self.cached_schedule:
            self.update_weekly_data()
        return self.cached_schedule