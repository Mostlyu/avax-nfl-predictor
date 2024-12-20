from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Get database URL from Railway
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class TeamMapping(Base):
    __tablename__ = 'team_mapping'

    team_identifier = Column(String, primary_key=True)
    team_id = Column(Integer)
    team_name = Column(String)
    last_updated = Column(DateTime, default=datetime.now(datetime.timezone.utc))

def init_db():
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise