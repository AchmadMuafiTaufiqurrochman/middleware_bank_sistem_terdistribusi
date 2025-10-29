# app/db/database.py
"""
Database configuration untuk Middleware
Menggunakan SQLAlchemy dengan async support
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import Config
import urllib.parse

# Load configuration
config = Config()

# Encode password untuk URL
encoded_password = urllib.parse.quote_plus(config.DB_PASSWORD)

# Format URL koneksi database MySQL (async)
DATABASE_URL = (
    f"mysql+aiomysql://{config.DB_USER}:{encoded_password}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
)

# Membuat engine asynchronous
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,  # Set False di production
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20  # Max connections beyond pool_size
)

# Session factory (tiap request API pakai session sendiri)
async_session = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base untuk deklarasi model
Base = declarative_base()

# Dependency FastAPI (untuk inject ke route)
async def get_db():
    """Dependency untuk mendapatkan database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
