# scripts/test_service_connection.py
"""
Test koneksi ke Service Layer
"""
import asyncio
from app.services.service_client import ServiceClient
from app.config import Config

async def test_service_connection():
    print("🔍 Testing connection to Service Layer...")
    print(f"Service URL: {Config.SERVICE_URL}")
    print(f"Username: {Config.SERVICE_AUTH_USERNAME}")
    print()
    
    client = ServiceClient()
    
    try:
        # Test 1: Login
        print("1️⃣ Testing login...")
        try:
            result = await client.login(
                Config.SERVICE_AUTH_USERNAME,
                Config.SERVICE_AUTH_PASSWORD
            )
            print("✅ Login successful!")
            print(f"   Response: {result}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return
        
        print()
        
        # Test 2: Get Balance
        print("2️⃣ Testing get balance...")
        try:
            result = await client.get_balance()
            print("✅ Get balance successful!")
            print(f"   Response: {result}")
        except Exception as e:
            print(f"⚠️ Get balance failed: {e}")
        
        print()
        
        # Test 3: Get Customer Detail
        print("3️⃣ Testing get customer detail...")
        try:
            result = await client.get_customer_detail()
            print("✅ Get customer detail successful!")
            print(f"   Response: {result}")
        except Exception as e:
            print(f"⚠️ Get customer detail failed: {e}")
        
        print()
        print("✅ Service connection tests completed!")
        
    except Exception as e:
        print(f"❌ Service connection test failed!")
        print(f"Error: {e}")
        print("\n💡 Make sure:")
        print("  1. Service is running on", Config.SERVICE_URL)
        print("  2. Credentials in .env are correct:")
        print(f"     SERVICE_AUTH_USERNAME={Config.SERVICE_AUTH_USERNAME}")
        print("     SERVICE_AUTH_PASSWORD=[hidden]")

if __name__ == "__main__":
    asyncio.run(test_service_connection())
