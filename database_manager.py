from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
import os
import logging

logger = logging.getLogger(__name__)

# Get database URL from Railway
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///nfl_data.db"  # Fallback for local development

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class TeamMapping(Base):
    __tablename__ = 'team_mapping'

    team_identifier = Column(String, primary_key=True)
    team_id = Column(Integer)
    team_name = Column(String)
    last_updated = Column(DateTime)

def init_db():
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise