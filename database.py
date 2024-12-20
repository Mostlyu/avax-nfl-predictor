# database.py
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL and log it (without sensitive info)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///nfl_data.db')
logger.info(f"Database type: {'postgresql' if 'postgresql' in DATABASE_URL else 'sqlite'}")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Converted postgres:// to postgresql://")

# Create engine with error handling
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=True
    )
    logger.info("Database engine created successfully")
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

# ... [keep your other model definitions] ...

def init_db():
    """Initialize database and create all tables"""
    try:
        logger.info("Starting database initialization...")

        # Log all table names that will be created
        tables = Base.metadata.tables.keys()
        logger.info(f"Preparing to create tables: {', '.join(tables)}")

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Verify tables were created
        inspector = engine.inspect(engine)
        created_tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(created_tables)}")

        # Specifically check for team_mapping table
        if 'team_mapping' in created_tables:
            logger.info("team_mapping table was created successfully")
        else:
            logger.error("team_mapping table was not created!")

        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        logger.error(f"Error type: {type(e)}")
        raise

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()