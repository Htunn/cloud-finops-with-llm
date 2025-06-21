#!/usr/bin/env python3
"""
Database initialization and setup script.
"""
import logging
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError
from dotenv import load_dotenv

from database.connection import SQLALCHEMY_DATABASE_URL
from database.models import Base
from config.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def create_schema(engine):
    """Create schema if it doesn't exist."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS finops;"))
            conn.commit()
            logger.info("Schema 'finops' created or already exists.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating schema: {e}")
        raise


def create_extensions(engine):
    """Create necessary PostgreSQL extensions."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            conn.commit()
            logger.info("Extension 'uuid-ossp' created or already exists.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating extension: {e}")
        raise


def create_tables(engine):
    """Create all database tables."""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        raise


def create_user_role(engine):
    """Create read-only user role for LLM access."""
    try:
        with engine.connect() as conn:
            # Check if role already exists
            result = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname='llm_reader'"))
            if not result.fetchone():
                # Create role
                conn.execute(text("CREATE ROLE llm_reader WITH LOGIN PASSWORD 'llm_secure_password';"))
                conn.execute(text(f"GRANT CONNECT ON DATABASE {Config.POSTGRES_DB} TO llm_reader;"))
                conn.execute(text("GRANT USAGE ON SCHEMA finops TO llm_reader;"))
                conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA finops TO llm_reader;"))
                conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA finops GRANT SELECT ON TABLES TO llm_reader;"))
                conn.commit()
                logger.info("Created 'llm_reader' role for database access.")
            else:
                logger.info("Role 'llm_reader' already exists.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating user role: {e}")
        logger.warning("Continuing with setup despite role creation error.")


def setup_database(drop_existing=False):
    """
    Set up the database.
    
    Args:
        drop_existing: If True, drop existing tables before creating new ones
    """
    try:
        # Create engine
        logger.info(f"Connecting to database at {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}...")
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        # Create schema
        create_schema(engine)
        
        # Create extensions
        create_extensions(engine)
        
        # Drop existing tables if requested
        if drop_existing:
            logger.warning("Dropping all existing tables...")
            Base.metadata.drop_all(engine)
            logger.info("Existing tables dropped.")
        
        # Create tables
        create_tables(engine)
        
        # Create user role
        create_user_role(engine)
        
        logger.info("Database setup completed successfully.")
    
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


def main():
    """Main function to set up the database."""
    parser = argparse.ArgumentParser(description="Set up the database for the FinOps application.")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables before creating new ones")
    
    args = parser.parse_args()
    
    try:
        setup_database(drop_existing=args.drop)
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
