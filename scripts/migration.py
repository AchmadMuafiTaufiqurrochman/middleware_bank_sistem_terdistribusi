# scripts/migration.py
"""
Database migration script untuk Middleware
Membuat semua table yang dibutuhkan
"""
import asyncio
from app.db.database import engine, Base
from app.db import models

async def migrate():
    """
    Jalankan migration untuk membuat semua table
    """
    print("🚀 Starting database migration...")
    print(f"Creating tables for middleware database...")

    async with engine.begin() as conn:
        # Drop all tables (hati-hati di production!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Migration completed successfully!")
    print("\nCreated tables:")
    print("  - transaction_logs")
    print("  - external_bank_status")
    print("  - service_credentials")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
