# scripts/test_connection.py
"""
Test database connection untuk middleware
"""
import asyncio
from sqlalchemy import text
from app.db.database import engine

async def test_connection():
    print("🔍 Testing middleware database connection...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()

            if value == 1:
                print("✅ Database connection successful!")
                
                # Test database name
                result = await conn.execute(text("SELECT DATABASE()"))
                db_name = result.scalar()
                print(f"📊 Connected to database: {db_name}")
            else:
                print("⚠️ Connected but unexpected result:", value)

    except Exception as e:
        print("❌ Database connection failed!")
        print("Error:", e)
        print("\n💡 Make sure:")
        print("  1. MySQL server is running")
        print("  2. Database credentials in .env are correct")
        print("  3. Database 'middleware' exists")
        print("  4. aiomysql is installed: pip install aiomysql")

    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())
