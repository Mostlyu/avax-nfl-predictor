# database.py
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set")

# Convert postgres:// to postgresql:// if necessary
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Converted postgres:// to postgresql:// in URL")

# Create engine with connection pooling
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

Base = declarative_base()

# Define models
class TeamStats(Base):
    __tablename__ = 'team_stats'

    game_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, primary_key=True)
    stat_name = Column(String, primary_key=True)
    stat_value = Column(Float)

class TeamMapping(Base):
    __tablename__ = 'team_mapping'

    team_identifier = Column(String, primary_key=True)
    team_id = Column(Integer)
    team_name = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

class QBStats(Base):
    __tablename__ = 'qb_stats'

    game_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, primary_key=True)
    player_id = Column(Integer)
    player_name = Column(String)
    stat_name = Column(String, primary_key=True)
    stat_value = Column(Float)

class MarketOdds(Base):
    __tablename__ = 'market_odds'

    game_id = Column(Integer, primary_key=True)
    bookmaker_id = Column(Integer, primary_key=True)
    bet_type = Column(String, primary_key=True)
    bet_value = Column(String, primary_key=True)
    odds = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)

class ConsensusLines(Base):
    __tablename__ = 'consensus_lines'

    game_id = Column(Integer, primary_key=True)
    line_type = Column(String, primary_key=True)
    consensus_value = Column(String)
    avg_odds = Column(Float)
    book_count = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)

class DataUpdates(Base):
    __tablename__ = 'data_updates'

    update_type = Column(String, primary_key=True)
    last_update = Column(DateTime)

class TeamPerformance(Base):
    __tablename__ = 'team_performance'

    team_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, primary_key=True)
    win_pct = Column(Float)
    points_per_game = Column(Float)
    last_game_date = Column(String)

class WeeklySchedule(Base):
    __tablename__ = 'weekly_schedule'

    game_id = Column(Integer, primary_key=True)
    date = Column(String)
    time = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    stadium = Column(String)
    city = Column(String)
    status = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

class GamePredictionsCache(Base):
    __tablename__ = 'game_predictions_cache'

    game_id = Column(Integer, primary_key=True)
    prediction_data = Column(Text)
    game_data = Column(Text)
    stats_data = Column(Text)
    odds_data = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow)
    expiry = Column(DateTime)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database by creating all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        # Test connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")

        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()