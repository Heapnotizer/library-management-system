from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session

from .config import DATABASE_URL

# Import all models to register them with SQLModel.metadata
# This ensures foreign key relationships are resolved correctly
from ..v1.authors.models import Author
from ..v1.books.models import Book

if DATABASE_URL == "":
    raise NotImplementedError("DATABASE_URL needs to be set")

# Create PostgreSQL engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections after 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully!")


def get_session():
    """Get database session - dependency for FastAPI"""
    with Session(engine) as session:
        yield session