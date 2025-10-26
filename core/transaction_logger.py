# Transaction Logger - Enhanced logging untuk audit trail
import logging
import json
from datetime import datetime
from typing import Dict, Optional
import mysql.connector
from mysql.connector import Error
import asyncio
from app.config import Config

logger = logging.getLogger(__name__)

class TransactionLogger:
    """
    Logger untuk mencatat semua transaksi yang melewati middleware
    Menyimpan ke database untuk audit trail
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    async def log_transaction(
        self,
        transaction_type: str,
        source_system: str,
        target_system: str,
        endpoint: str,
        request_payload: Dict,
        response_payload: Optional[Dict] = None,
        status_code: int = 0,
        duration_ms: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Log transaction to database
        
        Args:
            transaction_type: 'internal' | 'external' | 'inquiry'
            source_system: System yang meminta (e.g., 'service')
            target_system: System tujuan (e.g., 'core_bank', 'MINIBANK_A')
            endpoint: API endpoint yang dipanggil
            request_payload: Request data
            response_payload: Response data
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            error_message: Error message if failed
        """
        try:
            conn = await self._get_db_connection()
            cursor = conn.cursor()
            
            # Ensure table exists
            await self._ensure_tables_exist(cursor, conn)
            
            # Insert log
            query = """
                INSERT INTO transaction_logs 
                (transaction_type, source_system, target_system, endpoint, 
                 request_payload, response_payload, status_code, duration_ms, 
                 error_message, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                transaction_type,
                source_system,
                target_system,
                endpoint,
                json.dumps(request_payload, default=str),
                json.dumps(response_payload, default=str) if response_payload else None,
                status_code,
                duration_ms,
                error_message,
                datetime.now()
            )
            
            await asyncio.to_thread(cursor.execute, query, values)
            await asyncio.to_thread(conn.commit)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Transaction logged: {transaction_type} - {source_system} -> {target_system}")
            
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}")
    
    async def _get_db_connection(self):
        """Get database connection"""
        def _connect():
            return mysql.connector.connect(
                host=self.config.DB_HOST,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME
            )
        return await asyncio.to_thread(_connect)
    
    async def _ensure_tables_exist(self, cursor, conn):
        """Ensure required tables exist"""
        def _create_tables():
            # API logs table (existing)
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
            
            # Transaction logs table (new)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_logs (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    transaction_type VARCHAR(50) NOT NULL,
                    source_system VARCHAR(100) NOT NULL,
                    target_system VARCHAR(100) NOT NULL,
                    endpoint VARCHAR(255),
                    request_payload TEXT,
                    response_payload TEXT,
                    status_code INT,
                    duration_ms INT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_transaction_type (transaction_type),
                    INDEX idx_created_at (created_at),
                    INDEX idx_target_system (target_system)
                )
            """)
            
            # External bank status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS external_bank_status (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    bank_code VARCHAR(50) UNIQUE NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    failure_count INT DEFAULT 0,
                    last_error TEXT,
                    INDEX idx_bank_code (bank_code)
                )
            """)
            
            conn.commit()
        
        await asyncio.to_thread(_create_tables)
    
    async def get_transaction_stats(self, hours: int = 24) -> Dict:
        """
        Get transaction statistics for last N hours
        
        Returns:
            {
                'total_transactions': int,
                'internal_count': int,
                'external_count': int,
                'success_rate': float,
                'avg_duration_ms': float
            }
        """
        try:
            conn = await self._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN transaction_type = 'internal' THEN 1 ELSE 0 END) as internal_count,
                    SUM(CASE WHEN transaction_type = 'external' THEN 1 ELSE 0 END) as external_count,
                    SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as success_count,
                    AVG(duration_ms) as avg_duration
                FROM transaction_logs
                WHERE created_at >= NOW() - INTERVAL %s HOUR
            """
            
            await asyncio.to_thread(cursor.execute, query, (hours,))
            result = await asyncio.to_thread(cursor.fetchone)
            
            cursor.close()
            conn.close()
            
            if result and result['total'] > 0:
                return {
                    'total_transactions': result['total'],
                    'internal_count': result['internal_count'] or 0,
                    'external_count': result['external_count'] or 0,
                    'success_rate': (result['success_count'] / result['total']) * 100,
                    'avg_duration_ms': round(result['avg_duration'] or 0, 2)
                }
            
            return {
                'total_transactions': 0,
                'internal_count': 0,
                'external_count': 0,
                'success_rate': 0,
                'avg_duration_ms': 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get transaction stats: {e}")
            return {}

# Global logger instance
transaction_logger = TransactionLogger(Config())
