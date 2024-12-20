# weekly_manager.py
from datetime import datetime, timedelta
import requests
import logging
from sqlalchemy.orm import Session
from database import SessionLocal, TeamMapping, WeeklySchedule, TeamStats, MarketOdds, DataUpdates

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
            self.db = SessionLocal()
            self.init_team_mapping()
            logger.info("NFLWeeklyDataManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NFLWeeklyDataManager: {e}")
            raise
        finally:
            self.db.close()

    def init_team_mapping(self):
        """Initialize team mapping from API response"""
        try:
            # Check if we need to initialize
            existing_count = self.db.query(TeamMapping).count()
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
                logger.info(f"Team mapping already exists with {existing_count} entries")

        except Exception as e:
            logger.error(f"Failed to initialize team mapping: {e}")
            self.db.rollback()
            raise

    def needs_update(self) -> bool:
        """Check if data needs to be updated (weekly check)"""
        try:
            db = SessionLocal()
            result = db.query(DataUpdates).filter_by(update_type='weekly').first()

            if not result:
                logger.info("No previous update found, update needed")
                return True

            days_since_update = (datetime.now() - result.last_update).days
            logger.info(f"Days since last update: {days_since_update}")
            return days_since_update >= 7

        except Exception as e:
            logger.error(f"Error checking update status: {e}")
            return True
        finally:
            db.close()

    def get_cached_schedule(self):
        """Get schedule from cache"""
        try:
            db = SessionLocal()
            current_time = datetime.now()
            games = db.query(WeeklySchedule).filter(
                WeeklySchedule.date >= current_time.strftime('%Y-%m-%d')
            ).all()

            return [game.__dict__ for game in games]
        except Exception as e:
            logger.error(f"Error fetching cached schedule: {e}")
            return []
        finally:
            db.close()

    def update_weekly_data(self):
        """Update schedule if needed"""
        if not self.needs_update():
            logger.info("Schedule is up to date, using cached data")
            return self.get_cached_schedule()

        logger.info("Schedule update needed, fetching from API...")
        db = SessionLocal()
        try:
            # Clear existing schedule
            db.query(WeeklySchedule).delete()

            schedule = []
            for i in range(7):
                current_date = datetime.now() + timedelta(days=i)
                date = current_date.strftime('%Y-%m-%d')

                response = requests.get(
                    f"{self.base_url}/games",
                    headers=self.headers,
                    params={'league': '1', 'season': '2024', 'date': date}
                )
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
                    db.add(new_game)
                    schedule.append(game)

            # Update last update timestamp
            update_record = DataUpdates(
                update_type='weekly',
                last_update=datetime.utcnow()
            )
            db.merge(update_record)

            db.commit()
            logger.info("Schedule successfully updated and cached")
            return schedule

        except Exception as e:
            logger.error(f"Error updating weekly data: {e}")
            db.rollback()
            return []
        finally:
            db.close()

    async def cleanup(self):
        """Cleanup resources"""
        pass