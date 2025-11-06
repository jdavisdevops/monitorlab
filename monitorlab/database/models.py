"""Database models for run history tracking."""

import json
from datetime import datetime
from typing import Optional, Dict, Any, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from monitorlab.config.settings import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TestRun(Base):
    """Represents a complete test run with multiple agents."""

    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(50))  # running, completed, failed
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    results: Mapped[list["TestResult"]] = relationship(
        "TestResult", back_populates="test_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestRun(id={self.id}, name='{self.name}', status='{self.status}')>"


class TestResult(Base):
    """Represents an individual agent's test result within a run."""

    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_run_id: Mapped[int] = mapped_column(ForeignKey("test_runs.id"))
    agent_name: Mapped[str] = mapped_column(String(255))
    agent_type: Mapped[str] = mapped_column(String(100))
    task: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50))  # success, failure, error
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    output: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Relationships
    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="results")

    def __repr__(self) -> str:
        return f"<TestResult(id={self.id}, agent='{self.agent_name}', status='{self.status}')>"


# Database engine and session management
_engine = None
_async_session_maker = None


async def init_db(database_url: Optional[str] = None):
    """Initialize the database engine and create tables.

    Args:
        database_url: Database URL (default from settings)
    """
    global _engine, _async_session_maker

    if database_url is None:
        settings = get_settings()
        database_url = settings.database_url

    _engine = create_async_engine(database_url, echo=False)
    _async_session_maker = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Get an async database session.

    Yields:
        AsyncSession instance
    """
    if _async_session_maker is None:
        await init_db()

    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
