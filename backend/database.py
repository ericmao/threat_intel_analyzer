from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "threat_intel")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Elasticsearch configuration
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = os.getenv("ES_PORT", "9200")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASSWORD = os.getenv("ES_PASSWORD", "changeme")
ES_INDEX = "threat-intel"

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Elasticsearch client
es_client = Elasticsearch(
    [f"http://{ES_HOST}:{ES_PORT}"],
    basic_auth=(ES_USER, ES_PASSWORD)
)

Base = declarative_base()

@contextmanager
def get_db() -> Generator:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_es():
    """Initialize Elasticsearch index with mapping."""
    from models import es_threat_intel_mapping
    
    if not es_client.indices.exists(index=ES_INDEX):
        es_client.indices.create(
            index=ES_INDEX,
            body=es_threat_intel_mapping
        )
        print(f"Created Elasticsearch index: {ES_INDEX}")

def init_db():
    """Initialize database with tables."""
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("Initialized PostgreSQL database")

def get_es():
    """Get Elasticsearch client."""
    return es_client

# Database initialization function
def init():
    try:
        init_db()
        init_es()
        print("Database initialization completed successfully")
    except Exception as e:
        print(f"Error initializing databases: {e}")
        raise

# Health check functions
def check_postgres_connection():
    """Check PostgreSQL connection."""
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        return False

def check_es_connection():
    """Check Elasticsearch connection."""
    try:
        return es_client.ping()
    except Exception as e:
        print(f"Elasticsearch connection error: {e}")
        return False
