# database.py
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Get database URL from Railway or use SQLite for local development
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///nfl_data.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with error handling
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    logger.info(f"Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define models
class TeamMapping(Base):
    __tablename__ = 'team_mapping'

    team_identifier = Column(String, primary_key=True)
    team_id = Column(Integer)
    team_name = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database():
    conn = sqlite3.connect('nfl_data.db')
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS team_stats")
    cursor.execute("DROP TABLE IF EXISTS qb_stats")
    cursor.execute("DROP TABLE IF EXISTS team_mapping")
    cursor.execute("DROP TABLE IF EXISTS market_odds")
    cursor.execute("DROP TABLE IF EXISTS consensus_lines")
    cursor.execute("DROP TABLE IF EXISTS data_updates")
    cursor.execute("DROP TABLE IF EXISTS weekly_schedule")
    cursor.execute("DROP TABLE IF EXISTS team_performance")

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

    conn.commit()
    conn.close()
    print("Database created successfully")

def init_database():
    """Initialize database and return connection"""
    try:
        create_database()
        return sqlite3.connect('nfl_data.db')
    except Exception as e:
        print(f"Error initializing database: {e}")
        return None

def get_connection():
    """Get database connection"""
    try:
        return sqlite3.connect('nfl_data.db')
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

if __name__ == "__main__":
    create_database()