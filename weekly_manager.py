# weekly_manager.py
import requests
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, TeamMapping, WeeklySchedule, DataUpdates

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
                        logger.info(f"Added mapping for team: {name}")

                self.db.commit()
                logger.info("Team mapping initialization complete")
            else:
                logger.info("Team mapping already exists")

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Failed to initialize team mapping: {e}")
            self.db.rollback()
            raise

    def needs_update(self) -> bool:
        """Check if data needs to be updated (weekly check)"""
        try:
            update_record = self.db.query(DataUpdates).filter_by(update_type='weekly').first()

            if not update_record:
                logger.info("No previous update found")
                return True

            days_since_update = (datetime.now() - update_record.last_update).days
            logger.info(f"Days since last update: {days_since_update}")
            return days_since_update >= 7

        except Exception as e:
            logger.error(f"Error checking update status: {e}")
            return True

    def get_cached_schedule(self):
        """Get schedule from cache"""
        try:
            current_time = datetime.now()
            schedule = self.db.query(WeeklySchedule).filter(
                WeeklySchedule.date >= current_time.strftime('%Y-%m-%d')
            ).all()

            return [
                {
                    'id': game.game_id,
                    'date': game.date,
                    'time': game.time,
                    'home_team': game.home_team,
                    'away_team': game.away_team,
                    'stadium': game.stadium,
                    'city': game.city,
                    'status': game.status
                }
                for game in schedule
            ]
        except Exception as e:
            logger.error(f"Error fetching cached schedule: {e}")
            return []

    def update_weekly_data(self):
        """Update schedule if needed"""
        if not self.needs_update():
            logger.info("Schedule is up to date")
            return self.get_cached_schedule()

        logger.info("Schedule update needed, fetching from API...")
        try:
            # Clear existing schedule
            self.db.query(WeeklySchedule).delete()

            schedule = []
            for i in range(7):
                current_date = datetime.now() + timedelta(days=i)
                date = current_date.strftime('%Y-%m-%d')

                response = requests.get(
                    f"{self.base_url}/games",
                    headers=self.headers,
                    params={'league': '1', 'season': '2024', 'date': date}
                )
                response.raise_for_status()
                games = response.json().get('response', [])

                for game in games:
                    new_game = WeeklySchedule(
                        game_id=game['game']['id'],
                        date=game['game']['date']['date'],
                        time=game['game'].get('time', ''),
                        home_team=game['teams']['home']['name'],
                        away_team=game['teams']['away']['name'],
                        stadium=game['game'].get('venue', {}).get('name', ''),
                        city=game['game'].get('venue', {}).get('city', ''),
                        status=game['game']['status'].get('long', ''),
                        last_updated=datetime.utcnow()
                    )
                    self.db.add(new_game)
                    schedule.append(game)

            # Update last update timestamp
            self.db.merge(DataUpdates(
                update_type='weekly',
                last_update=datetime.utcnow()
            ))

            self.db.commit()
            logger.info("Schedule successfully updated")
            return schedule

        except Exception as e:
            logger.error(f"Error updating weekly data: {e}")
            self.db.rollback()
            return []

    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'db'):
            self.db.close()