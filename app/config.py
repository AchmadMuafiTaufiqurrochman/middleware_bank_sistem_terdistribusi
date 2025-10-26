# Configuration for Middleware
import os
import secrets
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Security - MUST be set in environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in environment variables!")
    
    # Database Configuration - MUST be set in environment variables
    DB_HOST = os.environ.get('DB_HOST')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME', 'middleware')
    
    # Validate required environment variables
    if not all([DB_HOST, DB_USER, DB_PASSWORD]):
        raise ValueError("DB_HOST, DB_USER, and DB_PASSWORD must be set in environment variables!")
    
    # Core Bank Configuration
    CORE_URL = os.environ.get('CORE_URL')
    if not CORE_URL:
        raise ValueError("CORE_URL must be set in environment variables!")
    
    # Rate Limiting
    RATE_LIMIT = int(os.environ.get('RATE_LIMIT', '100'))  # requests per minute
    TIMEOUT = int(os.environ.get('TIMEOUT', '10'))  # seconds
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_THRESHOLD = int(os.environ.get('CIRCUIT_BREAKER_THRESHOLD', '5'))  # failures before opening circuit
    CIRCUIT_BREAKER_TIMEOUT = int(os.environ.get('CIRCUIT_BREAKER_TIMEOUT', '60'))  # seconds before retry
    
    # External Banks Configuration
    # Format: {bank_code: {url, api_key, enabled}}
    # All API keys MUST be set in environment variables
    EXTERNAL_BANKS: Dict[str, Dict] = {
        'MINIBANK_A': {
            'url': os.environ.get('MINIBANK_A_URL', 'https://minibank-a.example.com'),
            'api_key': os.environ.get('MINIBANK_A_API_KEY'),
            'enabled': os.environ.get('MINIBANK_A_ENABLED', 'true').lower() == 'true',
            'timeout': int(os.environ.get('MINIBANK_A_TIMEOUT', '15'))
        },
        'MINIBANK_B': {
            'url': os.environ.get('MINIBANK_B_URL', 'https://minibank-b.example.com'),
            'api_key': os.environ.get('MINIBANK_B_API_KEY'),
            'enabled': os.environ.get('MINIBANK_B_ENABLED', 'true').lower() == 'true',
            'timeout': int(os.environ.get('MINIBANK_B_TIMEOUT', '15'))
        },
        # Add more external banks as needed
    }
    
    # Internal Bank Code
    INTERNAL_BANK_CODE = 'MINIBANK'
    INTERNAL_ACCOUNT_PREFIX = '1234'  # First 4 digits for internal accounts
    
    # Transaction Limits
    MAX_TRANSACTION_AMOUNT = 100000000  # 100 juta IDR
    MIN_TRANSACTION_AMOUNT = 10000  # 10 ribu IDR
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = 'logs/middleware.log'
    
    @classmethod
    def get_external_bank_config(cls, bank_code: str):
        """Get configuration for external bank by code"""
        return cls.EXTERNAL_BANKS.get(bank_code)
    
    @classmethod
    def is_internal_account(cls, account_number: str) -> bool:
        """Check if account number belongs to internal bank"""
        return account_number.startswith(cls.INTERNAL_ACCOUNT_PREFIX)