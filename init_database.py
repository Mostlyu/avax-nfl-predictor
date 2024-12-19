# init_database.py
import sqlite3
import requests
from config import API_KEY

def initialize_database():
    # Create database connection
    conn = sqlite3.connect('nfl_data.db')
    cursor = conn.cursor()

    # Create team_mapping table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team_mapping (
        team_identifier TEXT PRIMARY KEY,
        team_id INTEGER,
        team_name TEXT,
        last_updated TIMESTAMP
    )''')

    # API setup
    base_url = 'https://v1.american-football.api-sports.io'
    headers = {
        'x-rapidapi-host': 'v1.american-football.api-sports.io',
        'x-rapidapi-key': API_KEY
    }

    # Fetch teams from API
    try:
        response = requests.get(
            f"{base_url}/teams",
            headers=headers,
            params={'league': '1', 'season': '2024'}
        )
        teams = response.json()['response']

        # Insert teams into database
        for team in teams:
            # Skip if team name is missing
            if not team.get('name'):
                continue

            # Safely get team variations
            variations = []

            # Add full name if available
            if team.get('name'):
                variations.append(team['name'].lower())
                # Add nickname (last word of team name)
                variations.append(team['name'].split()[-1].lower())

            # Add city if available
            if team.get('city'):
                variations.append(team['city'].lower())

            # Filter out None values and duplicates
            variations = list(set([v for v in variations if v]))

            for variation in variations:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO team_mapping
                        (team_identifier, team_id, team_name, last_updated)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (variation, team['id'], team['name']))
                    print(f"Added mapping for: {variation} -> {team['name']}")
                except Exception as e:
                    print(f"Error adding mapping for {variation}: {e}")

        conn.commit()
        print("\nTeam mapping initialized successfully")

        # Verify data
        cursor.execute("SELECT COUNT(*) FROM team_mapping")
        count = cursor.fetchone()[0]
        print(f"Added {count} team mappings to database")

        # Show all mappings
        cursor.execute("SELECT team_identifier, team_name FROM team_mapping")
        mappings = cursor.fetchall()
        print("\nTeam mappings:")
        for mapping in mappings:
            print(f"{mapping[0]} -> {mapping[1]}")

    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()