"""
Database initialization and session management for Research Notebook Backend.

Provides SQLModel + SQLAlchemy integration for persistent storage of users,
sessions, and analysis history.
"""
import logging
from contextlib import contextmanager
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel, create_engine

logger = logging.getLogger(__name__)


def init_db(database_url: str) -> Engine:
    """
    Initialize the database engine and create all tables.
    
    Args:
        database_url: SQLAlchemy database URL (e.g., sqlite:///./test.db)
    
    Returns:
        SQLAlchemy Engine instance
    
    Raises:
        Exception: If database initialization fails
    """
    try:
        engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        )
        SQLModel.metadata.create_all(engine)
        logger.info(f"✅ Database initialized: {database_url}")
        return engine
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


def get_session_factory(engine: Engine) -> sessionmaker:
    """
    Create a session factory bound to the given engine.
    
    Args:
        engine: SQLAlchemy Engine instance
    
    Returns:
        sessionmaker instance for creating new sessions
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session(session_factory: sessionmaker) -> Session:
    """
    Context manager for database session handling.
    
    Usage:
        with get_session(session_factory) as session:
            # use session for queries
    
    Args:
        session_factory: sessionmaker instance
    
    Yields:
        SQLAlchemy Session instance
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


# Global database engine (initialized in main.py on startup)
_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def get_db() -> Session:
    """
    Dependency injection for FastAPI routes to get a database session.
    
    Usage in FastAPI route:
        from fastapi import Depends
        from backend.db import get_db
        
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            # use db session
    
    Yields:
        SQLAlchemy Session instance
    """
    global _session_factory
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() on startup.")
    
    session = _session_factory()
    try:
        yield session
    finally:
        session.close()


def set_engine(engine: Engine) -> None:
    """
    Set the global database engine (called during app startup).
    
    Args:
        engine: SQLAlchemy Engine instance
    """
    global _engine, _session_factory
    _engine = engine
    _session_factory = get_session_factory(engine)
    logger.info("Database engine configured globally.")
