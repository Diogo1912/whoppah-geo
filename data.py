"""
Data access layer for Whoppah GEO Monitor.

Handles SQLite database initialization and CRUD operations.
"""
from __future__ import annotations

from datetime import datetime, date
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).with_name("whoppah_geo.db")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, expire_on_commit=False)
Base = declarative_base()


class QueryResult(Base):
    """SQLAlchemy model for a single query run result."""

    __tablename__ = "query_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    query = Column(String, nullable=False)

    whoppah_mentioned = Column(Boolean, nullable=False, default=False)
    chairish_mentioned = Column(Boolean, nullable=False, default=False)  # Kept for backward compatibility
    context_category = Column(String, nullable=False, default="General")  # New field for context tracking

    sentiment = Column(String, nullable=False)  # Positive, Negative, Neutral
    excerpt = Column(String(200), nullable=False)
    full_response = Column(Text, nullable=False)


# ---------------------------------------------------------------------------
# Database migration helpers
# ---------------------------------------------------------------------------


def _migrate_database() -> None:
    """Add missing columns to existing database."""
    
    with SessionLocal() as session:
        try:
            # Check if context_category column exists
            result = session.execute(text("PRAGMA table_info(query_results)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "context_category" not in columns:
                # Add the missing column
                session.execute(text(
                    "ALTER TABLE query_results ADD COLUMN context_category VARCHAR DEFAULT 'General'"
                ))
                session.commit()
                print("✅ Added context_category column to database")
                
        except OperationalError as e:
            print(f"Database migration error: {e}")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create the SQLite database and tables if they do not exist."""

    Base.metadata.create_all(bind=ENGINE)
    _migrate_database()


def add_result(
    *,
    timestamp: datetime,
    query: str,
    whoppah_mentioned: bool,
    chairish_mentioned: bool,
    sentiment: str,
    excerpt: str,
    full_response: str,
    context_category: str = "General",
) -> None:
    """Persist a single query result to the database."""

    with SessionLocal() as session:
        result = QueryResult(
            timestamp=timestamp,
            query=query,
            whoppah_mentioned=whoppah_mentioned,
            chairish_mentioned=chairish_mentioned,
            context_category=context_category,
            sentiment=sentiment,
            excerpt=excerpt,
            full_response=full_response,
        )
        session.add(result)
        session.commit()


def get_results(
    *,
    start: Optional[date] = None,
    end: Optional[date] = None,
) -> pd.DataFrame:
    """Return results in the provided date range as a pandas DataFrame."""

    with SessionLocal() as session:
        query_stmt = session.query(QueryResult)
        if start:
            query_stmt = query_stmt.filter(QueryResult.timestamp >= datetime.combine(start, datetime.min.time()))
        if end:
            query_stmt = query_stmt.filter(QueryResult.timestamp <= datetime.combine(end, datetime.max.time()))

        df = pd.read_sql(query_stmt.statement, session.bind)
    return df


def get_latest_excerpts(*, limit: int = 10) -> pd.DataFrame:
    """Return the most recent excerpts as a pandas DataFrame."""

    with SessionLocal() as session:
        stmt = (
            session.query(
                QueryResult.timestamp,
                QueryResult.query,
                QueryResult.whoppah_mentioned,
                QueryResult.context_category,
                QueryResult.sentiment,
                QueryResult.excerpt,
            )
            .order_by(QueryResult.timestamp.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        df = pd.read_sql(stmt.statement, session.bind)
    return df 