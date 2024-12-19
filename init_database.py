# init_database.py
import sqlite3
import requests
import os
from config import API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    logger.info("Starting database initialization...")

    # Use absolute path for database
    db_path = os.path.join(os.getcwd(), 'nfl_data.db')
    logger.info(f"Using database path: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info("Creating tables...")
        # Create team_mapping table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_mapping (
            team_identifier TEXT PRIMARY KEY,
            team_id INTEGER,
            team_name TEXT,
            last_updated TIMESTAMP
        )''')

        logger.info("Fetching teams from API...")
        base_url = 'https://v1.american-football.api-sports.io'
        headers = {
            'x-rapidapi-host': 'v1.american-football.api-sports.io',
            'x-rapidapi-key': API_KEY
        }

        response = requests.get(
            f"{base_url}/teams",
            headers=headers,
            params={'league': '1', 'season': '2024'}
        )
        teams = response.json()['response']
        logger.info(f"Fetched {len(teams)} teams from API")

        # Insert teams
        for team in teams:
            if not team.get('name'):
                continue

            logger.info(f"Adding team: {team['name']}")
            cursor.execute('''
                INSERT OR REPLACE INTO team_mapping
                (team_identifier, team_id, team_name, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (team['name'].lower(), team['id'], team['name']))

        conn.commit()
        logger.info("Database initialization complete")

        # Verify data
        cursor.execute("SELECT COUNT(*) FROM team_mapping")
        count = cursor.fetchone()[0]
        logger.info(f"Verified {count} teams in database")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()