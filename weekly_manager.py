# weekly_manager.py
from datetime import datetime, timedelta
import requests
import logging
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from database import SessionLocal, TeamMapping, WeeklySchedule

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
        """Cleanup resources"""
        if hasattr(self, 'db'):
            self.db.close()

    def init_team_mapping(self):
        """Initialize team mapping from API response"""
        try:
            # Check if we need to initialize
            logger.info("Checking team mapping...")
            # Use SQLAlchemy ORM query
            existing_count = self.db.query(TeamMapping).count()
            logger.info(f"Found {existing_count} existing team mappings")

            if existing_count == 0:
                logger.info("Fetching teams from API...")
                response = requests.get(
                    f"{self.base_url}/teams",
                    headers=self.headers,
                    params={'league': '1', 'season': '2024'}
                )
                response.raise_for_status()

                teams = response.json().get('response', [])
                logger.info(f"Fetched {len(teams)} teams from API")

                for team in teams:
                    if name := team.get('name'):
                        mapping = TeamMapping(
                            team_identifier=name.lower(),
                            team_id=team.get('id'),
                            team_name=name,
                            last_updated=datetime.utcnow()
                        )
                        self.db.add(mapping)

                self.db.commit()
                logger.info("Team mapping initialized successfully")
            else:
                logger.info("Team mapping already exists")

        except Exception as e:
            logger.error(f"Failed to initialize team mapping: {e}")
            self.db.rollback()
            raise

    def update_weekly_data(self):
        """Update weekly data if needed"""
        current_time = datetime.now()

        # Only update if cache is empty or older than 6 hours
        if (not self.cached_schedule or
            not self.last_update or
            (current_time - self.last_update) > timedelta(hours=6)):

            try:
                # Get current NFL season
                current_year = datetime.now().year
                season = current_year if datetime.now().month > 6 else current_year - 1

                # Fetch next 7 days of games
                start_date = datetime.now().strftime('%Y-%m-%d')
                end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

                response = requests.get(
                    f"{self.base_url}/games",
                    headers=self.headers,
                    params={
                        "league": "1",  # NFL league ID
                        "season": str(season),
                        "date": start_date
                    }
                )
                response.raise_for_status()

                games_data = response.json()

                if games_data.get("response"):
                    formatted_games = []
                    for game in games_data["response"]:
                        game_date = datetime.strptime(game["game"]["date"]["date"], "%Y-%m-%d")
                        game_time = game["game"]["date"]["time"]

                        formatted_game = {
                            "id": game["game"]["id"],
                            "date": game_date.strftime("%Y-%m-%d"),
                            "time": game_time,
                            "home_team": game["teams"]["home"]["name"],
                            "away_team": game["teams"]["away"]["name"],
                            "stadium": game["game"]["venue"]["name"],
                            "city": game["game"]["venue"]["city"],
                            "status": game["game"]["status"]["long"]
                        }
                        formatted_games.append(formatted_game)

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

    def get_cached_schedule(self):
        """Get the cached schedule"""
        if not self.cached_schedule:
            self.update_weekly_data()
        return self.cached_schedule