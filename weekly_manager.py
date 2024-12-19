# weekly_manager.py

from datetime import datetime, timedelta
import sqlite3
import requests
import logging
import os

logger = logging.getLogger(__name__)

class NFLWeeklyDataManager:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API_KEY is not set in environment variables")
        self.api_key = api_key
        logger.info("Initializing NFLWeeklyDataManager")
        self.api_key = api_key
        self.base_url = 'https://v1.american-football.api-sports.io'
        self.headers = {
            'x-rapidapi-host': 'v1.american-football.api-sports.io',
            'x-rapidapi-key': api_key
        }
        self.db_path = os.path.join(os.getcwd(), 'nfl_data.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist
        self.create_tables()
        self.init_team_mapping()

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            logger.info("Creating tables if they don't exist...")
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_mapping (
                team_identifier TEXT PRIMARY KEY,
                team_id INTEGER,
                team_name TEXT,
                last_updated TIMESTAMP
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_stats (
                game_id INTEGER,
                team_id INTEGER,
                stat_name TEXT,
                stat_value REAL,
                PRIMARY KEY (game_id, team_id, stat_name)
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_schedule (
                game_id INTEGER PRIMARY KEY,
                date TEXT,
                time TEXT,
                home_team TEXT,
                away_team TEXT,
                stadium TEXT,
                city TEXT,
                status TEXT,
                last_updated TIMESTAMP
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_updates (
                update_type TEXT PRIMARY KEY,
                last_update TIMESTAMP
            )''')

            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_odds (
                game_id INTEGER,
                bookmaker_id INTEGER,
                bet_type TEXT,
                bet_value TEXT,
                odds REAL,
                last_updated TIMESTAMP,
                PRIMARY KEY (game_id, bookmaker_id, bet_type, bet_value)
            )''')

            self.conn.commit()
            logger.info("Tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def needs_update(self) -> bool:
        """Check if data needs to be updated (weekly check)"""
        try:
            self.cursor.execute('''
                SELECT last_update
                FROM data_updates
                WHERE update_type = 'weekly'
            ''')
            result = self.cursor.fetchone()

            if not result:
                logger.info("No previous update found, update needed")
                return True

            last_update = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            days_since_update = (datetime.now() - last_update).days

            # Log when the next update will be needed
            logger.info(f"Days since last update: {days_since_update}")
            logger.info(f"Next update in: {7 - days_since_update} days")

            return days_since_update >= 7

        except Exception as e:
            logger.error(f"Error checking update status: {e}")
            return True

    def get_cached_schedule(self):
        """Get schedule from cache"""
        try:
            logger.info("Attempting to fetch schedule from cache...")
            self.cursor.execute('''
                SELECT
                    game_id, date, time, home_team, away_team,
                    stadium, city, status
                FROM weekly_schedule
                WHERE datetime(date || ' ' || COALESCE(time, '00:00')) > datetime('now')
                ORDER BY date, time
            ''')

            games = self.cursor.fetchall()
            logger.info(f"Found {len(games)} games in cache")
            schedule_list = []

            for game in games:
                schedule_list.append({
                    'id': game[0],
                    'date': game[1],
                    'time': game[2],
                    'home_team': game[3],
                    'away_team': game[4],
                    'stadium': game[5],
                    'city': game[6],
                    'status': game[7]
                })

            return schedule_list

        except Exception as e:
            logger.error(f"Error fetching cached schedule: {e}")
            return []

    def update_weekly_data(self):
        """Update schedule if needed"""
        # First check if we need to update
        if not self.needs_update():
            logger.info("Schedule is up to date, using cached data")
            return

        logger.info("Schedule update needed, fetching from API...")
        try:
            # Clear existing schedule before update
            self.cursor.execute('DELETE FROM weekly_schedule')

            schedule = []
            # Fetch next 7 days of games
            for i in range(7):
                current_date = datetime.now() + timedelta(days=i)
                date = current_date.strftime('%Y-%m-%d')

                url = f"{self.base_url}/games"
                params = {
                    'league': '1',
                    'season': '2024',
                    'date': date
                }

                response = requests.get(url, headers=self.headers, params=params)
                games = response.json().get('response', [])

                for game in games:
                    game_id = game['game']['id']
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO weekly_schedule
                        (game_id, date, time, home_team, away_team, stadium, city, status, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ''', (
                        game_id,
                        game['game']['date']['date'],
                        game['game'].get('time', ''),
                        game['teams']['home']['name'],
                        game['teams']['away']['name'],
                        game['game'].get('venue', {}).get('name', ''),
                        game['game'].get('venue', {}).get('city', ''),
                        game['game']['status'].get('long', '')
                    ))
                    schedule.append(game)

            # Update last update timestamp
            self.cursor.execute('''
                INSERT OR REPLACE INTO data_updates (update_type, last_update)
                VALUES ('weekly', datetime('now'))
            ''')

            self.conn.commit()
            logger.info("Schedule successfully updated and cached")
            return schedule

        except Exception as e:
            logger.error(f"Error updating weekly data: {e}")
            self.conn.rollback()
            return []

    def get_cached_team_stats(self, team_name: str) -> dict:
        """Get team stats from cache"""
        try:
            logger.info(f"Attempting to get cached stats for {team_name}")
            self.cursor.execute('''
                SELECT stat_name, stat_value
                FROM team_stats
                WHERE team_id = (
                    SELECT team_id
                    FROM team_mapping
                    WHERE team_name = ?
                )
            ''', (team_name,))

            stats = self.cursor.fetchall()
            if stats:
                logger.info(f"Found cached stats for {team_name}")
                return {stat[0]: stat[1] for stat in stats}
            logger.info(f"No cached stats found for {team_name}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching cached team stats: {e}")
            return {}

    def cache_team_stats(self, team_name: str, team_stats: dict):
        """Cache team stats"""
        try:
            # Get team ID from team mapping
            self.cursor.execute('''
                SELECT team_id
                FROM team_mapping
                WHERE team_name = ?
            ''', (team_name,))
            result = self.cursor.fetchone()
            if not result:
                logger.error(f"Team not found in mapping: {team_name}")
                return

            team_id = result[0]

            # Delete existing stats for this team
            self.cursor.execute('''
                DELETE FROM team_stats
                WHERE team_id = ?
            ''', (team_id,))

            # Insert new stats
            for stat_name, stat_value in team_stats.items():
                if stat_name != 'game_id':  # Skip game_id
                    try:
                        self.cursor.execute('''
                            INSERT INTO team_stats
                            (team_id, stat_name, stat_value)
                            VALUES (?, ?, ?)
                        ''', (team_id, stat_name, float(stat_value)))
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error inserting stat {stat_name}: {e}")
                        continue

            self.conn.commit()
        except Exception as e:
            logger.error(f"Error caching team stats: {e}")
            self.conn.rollback()

    def get_cached_game(self, game_id: int) -> dict:
        """Get game information from cache"""
        try:
            self.cursor.execute('''
                SELECT
                    game_id, date, time, home_team, away_team,
                    stadium, city, status
                FROM weekly_schedule
                WHERE game_id = ?
            ''', (game_id,))

            game = self.cursor.fetchone()

            if game:
                return {
                    'id': game[0],
                    'date': game[1],
                    'time': game[2],
                    'home_team': game[3],
                    'away_team': game[4],
                    'stadium': game[5],
                    'city': game[6],
                    'status': game[7]
                }
            return None

        except Exception as e:
            logger.error(f"Error fetching cached game: {e}")
            return None

    def get_team_id(self, team_name: str) -> int:
        """Get team ID from team name"""
        try:
            self.cursor.execute('''
                SELECT team_id
                FROM team_mapping
                WHERE team_name = ?
            ''', (team_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting team ID: {e}")
            return None

    def get_cached_odds(self, game_id: int) -> dict:
        """Get cached odds for a game"""
        try:
            self.cursor.execute('''
                SELECT bet_type, bet_value, odds
                FROM market_odds
                WHERE game_id = ?
            ''', (game_id,))

            odds = self.cursor.fetchall()
            if not odds:
                return None

            processed_odds = {
                'spread': {},
                'total': {},
                'moneyline': {}
            }

            for bet_type, bet_value, odd in odds:
                processed_odds[bet_type][bet_value] = odd

            return processed_odds
        except Exception as e:
            logger.error(f"Error fetching cached odds: {e}")
            return None

    def cache_odds(self, game_id: int, odds_data: dict):
        """Cache odds data"""
        try:
            # Clear existing odds for this game
            self.cursor.execute('''
                DELETE FROM market_odds
                WHERE game_id = ?
            ''', (game_id,))

            # Insert new odds
            for bet_type, bets in odds_data.items():
                for bet_value, odd in bets.items():
                    self.cursor.execute('''
                        INSERT INTO market_odds
                        (game_id, bet_type, bet_value, odds, last_update)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    ''', (game_id, bet_type, bet_value, odd))

            self.conn.commit()
        except Exception as e:
            logger.error(f"Error caching odds: {e}")
            self.conn.rollback()

    def init_team_mapping(self):
        """Initialize team mapping from API response"""
        try:
            # First verify table exists
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_mapping (
                team_identifier TEXT PRIMARY KEY,
                team_id INTEGER,
                team_name TEXT,
                last_updated TIMESTAMP
            )''')
            self.conn.commit()
            logger.info("Team mapping table verified/created")

            # Verify table is empty before adding data
            self.cursor.execute("SELECT COUNT(*) FROM team_mapping")
            count = self.cursor.fetchone()[0]
            logger.info(f"Current team mappings in database: {count}")

            # Only fetch from API if table is empty
            if count == 0:
                logger.info("Fetching teams from API...")
                url = f"{self.base_url}/teams"
                params = {'league': '1', 'season': '2024'}

                try:
                    response = requests.get(url, headers=self.headers, params=params)
                    response.raise_for_status()  # Raise exception for bad status codes
                    data = response.json()
                    teams = data.get('response', [])
                    logger.info(f"Fetched {len(teams)} teams from API")

                    if not teams:
                        logger.error("No teams returned from API")
                        return

                    # Insert teams one by one with error handling
                    for team in teams:
                        try:
                            name = team.get('name')
                            team_id = team.get('id')
                            if name and team_id:
                                self.cursor.execute('''
                                    INSERT OR REPLACE INTO team_mapping
                                    (team_identifier, team_id, team_name, last_updated)
                                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                ''', (name.lower(), team_id, name))
                                logger.info(f"Added team: {name}")
                        except sqlite3.Error as e:
                            logger.error(f"Error inserting team {team.get('name')}: {e}")
                            continue

                    self.conn.commit()
                    logger.info("Team mapping initialization complete")

                except requests.RequestException as e:
                    logger.error(f"API request failed: {e}")
                    raise
                except ValueError as e:
                    logger.error(f"JSON parsing failed: {e}")
                    raise

        except sqlite3.Error as e:
            logger.error(f"Database error in init_team_mapping: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in init_team_mapping: {e}")
            logger.error(f"Error type: {type(e)}")
            raise