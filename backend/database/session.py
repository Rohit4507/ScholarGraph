"""
ScholarGraph AI — Database Session Management
SQLAlchemy engine, session factory, and database initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings

settings = get_settings()

# ── Engine ──────────────────────────────────────────────────────
db_url = settings.POSTGRES_URL or settings.DATABASE_URL

engine = create_engine(
    db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
)

# ── Session Factory ─────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base Class ──────────────────────────────────────────────────
Base = declarative_base()


def get_db():
    """Dependency: yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in ORM models."""
    from database.models import Base as ModelsBase  # noqa: F401
    ModelsBase.metadata.create_all(bind=engine)
