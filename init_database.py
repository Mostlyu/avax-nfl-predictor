# init_database.py
import sqlite3
import requests
from config import API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    logger.info("Starting database initialization...")
    try:
        conn = sqlite3.connect('nfl_data.db')
        cursor = conn.cursor()

        # Create tables without dropping them
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_stats (
            game_id INTEGER,
            team_id INTEGER,
            stat_name TEXT,
            stat_value REAL,
            PRIMARY KEY (game_id, team_id, stat_name)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_mapping (
            team_identifier TEXT PRIMARY KEY,
            team_id INTEGER,
            team_name TEXT,
            last_updated TIMESTAMP
        )''')

        # Add other table creations here...
         # Create team_stats table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_stats (
            game_id INTEGER,
            team_id INTEGER,
            stat_name TEXT,
            stat_value REAL,
            PRIMARY KEY (game_id, team_id, stat_name)
        )''')

        # Create team_mapping table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_mapping (
            team_identifier TEXT PRIMARY KEY,
            team_id INTEGER,
            team_name TEXT,
            last_updated TIMESTAMP
        )''')

        # Create QB stats table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS qb_stats (
            game_id INTEGER,
            team_id INTEGER,
            player_id INTEGER,
            player_name TEXT,
            stat_name TEXT,
            stat_value REAL,
            PRIMARY KEY (game_id, team_id, stat_name)
        )''')

        # Create market odds table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_odds (
            game_id INTEGER,
            bookmaker_id INTEGER,
            bet_type TEXT,
            bet_value TEXT,
            odds REAL,
            last_updated TIMESTAMP,
            PRIMARY KEY (game_id, bookmaker_id, bet_type, bet_value)
        )''')

        # Create consensus lines table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS consensus_lines (
            game_id INTEGER,
            line_type TEXT,
            consensus_value TEXT,
            avg_odds REAL,
            book_count INTEGER,
            last_updated TIMESTAMP,
            PRIMARY KEY (game_id, line_type)
        )''')

        # Create data updates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_updates (
            update_type TEXT PRIMARY KEY,
            last_update TIMESTAMP
        )''')

        # Create team performance table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_performance (
            team_id INTEGER,
            game_id INTEGER,
            win_pct REAL,
            points_per_game REAL,
            last_game_date TEXT,
            PRIMARY KEY (team_id, game_id)
        )''')

        # Create weekly schedule table
        cursor.execute('''
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

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_predictions_cache (
            game_id INTEGER PRIMARY KEY,
            prediction_data TEXT,
            game_data TEXT,
            stats_data TEXT,
            odds_data TEXT,
            last_updated TIMESTAMP,
            expiry TIMESTAMP,
            CONSTRAINT game_predictions_cache_unique UNIQUE (game_id)
        )''')

        logger.info("Tables created successfully")

        # Initialize team mapping
        base_url = 'https://v1.american-football.api-sports.io'
        headers = {
            'x-rapidapi-host': 'v1.american-football.api-sports.io',
            'x-rapidapi-key': API_KEY
        }

        logger.info("Fetching teams from API...")
        response = requests.get(
            f"{base_url}/teams",
            headers=headers,
            params={'league': '1', 'season': '2024'}
        )
        teams = response.json()['response']

        # Insert teams into database
        for team in teams:
            if not team.get('name'):
                continue

            cursor.execute('''
                INSERT OR REPLACE INTO team_mapping
                (team_identifier, team_id, team_name, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (team['name'].lower(), team['id'], team['name']))
            logger.info(f"Added mapping for: {team['name']}")

        conn.commit()
        logger.info("Team mapping initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()