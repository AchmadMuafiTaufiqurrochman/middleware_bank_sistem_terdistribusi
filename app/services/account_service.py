# app/services/account_service.py
"""
Service untuk account management
"""
from typing import Dict, Any, Optional
from app.services.service_client import ServiceClient
import logging

logger = logging.getLogger(__name__)


class AccountService:
    """
    Service untuk handle account operations
    """
    
    def __init__(self):
        self.service_client = ServiceClient()
    
    async def get_account_balance(self, account_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account balance
        
        Args:
            account_number: Optional account number
            
        Returns:
            Balance information
        """
        try:
            result = await self.service_client.get_balance(account_number)
            return result
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            raise
    
    async def get_account_detail(self) -> Dict[str, Any]:
        """
        Get account detail
        
        Returns:
            Account detail information
        """
        try:
            result = await self.service_client.get_customer_detail()
            return result
        except Exception as e:
            logger.error(f"Error getting account detail: {e}")
            raise
