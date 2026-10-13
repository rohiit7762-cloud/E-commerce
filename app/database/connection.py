"""Database connection and session lifecycle management."""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.database.models import Base
from app.utils.logger import setup_logger

logger = setup_logger("db_connection")


def get_engine(database_url: Optional[str] = None) -> Engine:
    """
    Create and return a configured SQLAlchemy Engine.
    Supports SQLite and PostgreSQL dynamically without code modifications.

    Args:
        database_url: Optional override database connection URL.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """
    url = database_url or settings.DATABASE_URL

    connect_args = {}
    if url.startswith("sqlite"):
        # SQLite specific threading support
        connect_args["check_same_thread"] = False
        engine = create_engine(
            url,
            connect_args=connect_args,
            echo=False,
            future=True,
        )
    else:
        # PostgreSQL / production pool settings
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False,
            future=True,
        )

    logger.debug(f"Database engine initialized for dialect: {engine.dialect.name}")
    return engine


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a sessionmaker factory bound to the provided engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of database operations.
    Automatically commits on success or rolls back and re-raises on exception.
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction rolled back due to error: {e}")
        raise
    finally:
        session.close()


def init_db(engine: Engine) -> None:
    """
    Initialize relational database tables defined in SQLAlchemy ORM.
    Idempotent operation (uses CREATE TABLE IF NOT EXISTS).
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(engine)
    logger.info("Database schema initialized successfully.")
