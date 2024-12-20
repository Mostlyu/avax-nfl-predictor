# database.py
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Get database URL from Railway or use SQLite for local development
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///nfl_data.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with error handling
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=True  # This will log all SQL statements
    )
    logger.info(f"Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define all models
class TeamMapping(Base):
    __tablename__ = 'team_mapping'
    team_identifier = Column(String, primary_key=True)
    team_id = Column(Integer)
    team_name = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

class TeamStats(Base):
    __tablename__ = 'team_stats'
    game_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, primary_key=True)
    stat_name = Column(String, primary_key=True)
    stat_value = Column(Float)

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
    last_updated = Column(DateTime)

class MarketOdds(Base):
    __tablename__ = 'market_odds'
    game_id = Column(Integer, primary_key=True)
    bookmaker_id = Column(Integer, primary_key=True)
    bet_type = Column(String, primary_key=True)
    bet_value = Column(String, primary_key=True)
    odds = Column(Float)
    last_updated = Column(DateTime)

class DataUpdates(Base):
    __tablename__ = 'data_updates'
    update_type = Column(String, primary_key=True)
    last_update = Column(DateTime)

class GamePredictionsCache(Base):
    __tablename__ = 'game_predictions_cache'
    game_id = Column(Integer, primary_key=True)
    prediction_data = Column(Text)
    game_data = Column(Text)
    stats_data = Column(Text)
    odds_data = Column(Text)
    last_updated = Column(DateTime)
    expiry = Column(DateTime)

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
