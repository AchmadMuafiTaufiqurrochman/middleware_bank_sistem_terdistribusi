"""
Dependencies for FastAPI routes
Includes authentication, rate limiting, and database connections
"""

from fastapi import Header, HTTPException, Request, Depends
import asyncio
import time
import logging
import mysql.connector
from typing import Dict, List
from app.config import Config

config = Config()
logger = logging.getLogger(__name__)

# Rate limiting setup
request_counts: Dict[str, List[float]] = {}
rate_limit_lock = asyncio.Lock()

async def check_rate_limit(request: Request):
    """Check if request is within rate limit"""
    client_ip = request.client.host
    current_time = time.time()

    async with rate_limit_lock:
        if client_ip not in request_counts:
            request_counts[client_ip] = []

        # Remove old requests (older than 1 minute)
        request_counts[client_ip] = [req_time for req_time in request_counts[client_ip]
                                    if current_time - req_time < 60]

        if len(request_counts[client_ip]) >= config.RATE_LIMIT:
            return False

        request_counts[client_ip].append(current_time)
        return True

def authenticate(request: Request):
    """Authenticate requests using service token or Bearer token"""
    # Check X-Service-Token (legacy)
    token = request.headers.get('X-Service-Token')
    
    # Check Authorization Bearer token (standard)
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
    
    if not token or token != config.SECRET_KEY:
        return False
    return True

async def auth_dependency(request: Request):
    """Dependency for authentication and rate limiting"""
    if not await check_rate_limit(request):
        logger.warning(f'Rate limit exceeded for {request.client.host}')
        raise HTTPException(status_code=429, detail='Rate limit exceeded')

    if not authenticate(request):
        logger.warning(f'Unauthorized access attempt from {request.client.host}')
        raise HTTPException(status_code=401, detail='Unauthorized')

    return True

async def get_db_connection():
    """Get database connection for logging"""
    def _connect():
        try:
            conn = mysql.connector.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME
            )
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_system VARCHAR(100),
                    target_system VARCHAR(100),
                    endpoint VARCHAR(255),
                    request_payload TEXT,
                    response_payload TEXT,
                    status_code INT,
                    duration_ms INT
                )
            """)
            conn.commit()
            cursor.close()
            return conn
        except mysql.connector.Error as err:
            if err.errno == 1049:  # Database does not exist
                conn = mysql.connector.connect(
                    host=config.DB_HOST,
                    user=config.DB_USER,
                    password=config.DB_PASSWORD
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
                cursor.execute(f"USE {config.DB_NAME}")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        source_system VARCHAR(100),
                        target_system VARCHAR(100),
                        endpoint VARCHAR(255),
                        request_payload TEXT,
                        response_payload TEXT,
                        status_code INT,
                        duration_ms INT
                    )
                """)
                conn.commit()
                cursor.close()
                conn.close()
                return mysql.connector.connect(
                    host=config.DB_HOST,
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    database=config.DB_NAME
                )
            else:
                logger.error(f"Database connection error: {err}")
                raise
    return await asyncio.to_thread(_connect)
