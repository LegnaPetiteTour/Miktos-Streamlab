"""
Database Connection and Session Management

Provides database initialization, connection pooling, and session factory.
"""

import logging
from pathlib import Path
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from db.models import Base
from config import get_config

logger = logging.getLogger(__name__)


class Database:
    """
    Database connection manager.

    Handles SQLite connection, session factory, and schema initialization.

    Example:
        ```python
        db = Database()
        db.init_db()

        with db.session() as session:
            session.add(SessionModel(...))
            session.commit()
        ```
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False
    ):
        """
        Initialize database connection.

        Args:
            database_url: SQLite database URL (default: from config)
            echo: Enable SQL query logging
        """
        config = get_config()

        # Use provided URL or get from config
        if database_url is None:
            db_path = Path(config.paths.data_dir) / "miktos_hub.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = f"sqlite:///{db_path}"

        logger.info(f"Initializing database: {database_url}")

        # Create engine with connection pooling
        # For SQLite, use StaticPool to avoid threading issues
        self._engine = create_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},  # SQLite specific
            poolclass=StaticPool,  # Single connection pool for SQLite
        )

        # Enable foreign keys for SQLite
        if database_url.startswith("sqlite"):
            self._enable_sqlite_foreign_keys(self._engine)

        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )

        logger.info("Database connection established")

    @staticmethod
    def _enable_sqlite_foreign_keys(engine: Engine) -> None:
        """Enable foreign key constraints for SQLite"""
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def init_db(self) -> None:
        """
        Initialize database schema.

        Creates all tables defined in models.
        """
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self._engine)
        logger.info("Database tables created successfully")

    def drop_all(self) -> None:
        """
        Drop all database tables.

        WARNING: This deletes all data!
        """
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self._engine)
        logger.warning("All tables dropped")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Create a new database session context.

        Automatically commits on success, rolls back on error.

        Yields:
            Database session

        Example:
            ```python
            with db.session() as session:
                session.add(model)
                session.commit()
            ```
        """
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """
        Get a new database session.

        Note: Caller is responsible for closing the session.
        Prefer using session() context manager instead.

        Returns:
            Database session
        """
        return self._session_factory()

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine"""
        return self._engine

    def close(self) -> None:
        """Close database connection"""
        logger.info("Closing database connection")
        self._engine.dispose()


# Global database instance
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """
    Get global database instance.

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.init_db()
    return _db_instance


def init_database(
    database_url: Optional[str] = None, echo: bool = False
) -> Database:
    """
    Initialize global database instance.

    Args:
        database_url: Database URL (default: from config)
        echo: Enable SQL query logging

    Returns:
        Database instance
    """
    global _db_instance
    _db_instance = Database(database_url=database_url, echo=echo)
    _db_instance.init_db()
    return _db_instance


def close_database() -> None:
    """Close global database instance"""
    global _db_instance
    if _db_instance is not None:
        _db_instance.close()
        _db_instance = None
