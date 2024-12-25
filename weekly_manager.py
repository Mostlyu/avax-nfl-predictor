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

                response.raise_for_status()
                games_data = response.json()

                if games_data.get("response"):
                    formatted_games = []
                    for game in games_data["response"]:
                        try:
                            # Extract data from the correct nested structure
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
                        except KeyError as e:
                            logger.error(f"Error accessing game data: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Unexpected error formatting game: {e}")
                            continue

                    self.cached_schedule = formatted_games
                    self.last_update = current_time
                    logger.info(f"Updated schedule cache with {len(formatted_games)} games")
                else:
                    logger.warning("No games found in API response")
                    self.cached_schedule = []

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