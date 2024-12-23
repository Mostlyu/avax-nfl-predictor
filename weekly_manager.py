# weekly_manager.py
from datetime import datetime, timedelta
import requests
import logging
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from database import SessionLocal, TeamMapping, WeeklySchedule

logger = logging.getLogger(__name__)

class NFLWeeklyDataManager:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API_KEY is required")

        self.api_key = api_key
        self.base_url = 'https://v1.american-football.api-sports.io'
        self.headers = {
            'x-rapidapi-host': 'v1.american-football.api-sports.io',
            'x-rapidapi-key': api_key
        }

        # Initialize database on startup
        try:
            logger.info("Initializing NFLWeeklyDataManager")
            self.db = SessionLocal()
            self.init_team_mapping()
            logger.info("NFLWeeklyDataManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NFLWeeklyDataManager: {e}")
            raise
        finally:
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

    def get_cached_schedule(self):
        """Get schedule from cache"""
        try:
            current_time = datetime.now()
            # Query existing schedule from database
            schedule = self.db.query(WeeklySchedule)\
                .filter(WeeklySchedule.date >= current_time.strftime('%Y-%m-%d'))\
                .all()

            if schedule:
                return [{
                    "id": game.game_id,
                    "date": game.date,
                    "time": game.time,
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "stadium": game.stadium,
                    "city": game.city,
                    "status": game.status
                } for game in schedule]

            # Return mock data if no schedule in database
            return [
                {
                    "id": 1,
                    "date": "2024-12-24",
                    "time": "20:00",
                    "home_team": "Kansas City Chiefs",
                    "away_team": "Las Vegas Raiders",
                    "stadium": "Arrowhead Stadium",
                    "city": "Kansas City",
                    "status": "Not Started"
                },
                {
                    "id": 2,
                    "date": "2024-12-25",
                    "time": "16:30",
                    "home_team": "San Francisco 49ers",
                    "away_team": "Baltimore Ravens",
                    "stadium": "Levi's Stadium",
                    "city": "Santa Clara",
                    "status": "Not Started"
                }
            ]
        except Exception as e:
            logger.error(f"Error fetching cached schedule: {e}")
            return []

    def update_weekly_data(self):
        """Update schedule if needed"""
        return True

    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'db'):
            self.db.close()