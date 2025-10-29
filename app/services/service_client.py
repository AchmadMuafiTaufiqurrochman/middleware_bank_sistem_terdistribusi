# app/services/service_client.py
"""
Client untuk berkomunikasi dengan Service Layer
Menggunakan header authentication sesuai dengan service
"""
import httpx
from typing import Dict, Any, Optional
from app.config import Config
import logging

logger = logging.getLogger(__name__)


class ServiceClient:
    """
    Client untuk memanggil Service Layer dengan autentikasi header
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.base_url = self.config.SERVICE_URL
        self.username = self.config.SERVICE_AUTH_USERNAME
        self.password = self.config.SERVICE_AUTH_PASSWORD
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Generate headers dengan Authorization-Username dan Authorization-Password
        sesuai dengan format yang diharapkan service
        """
        return {
            "Content-Type": "application/json",
            "Authorization-Username": self.username,
            "Authorization-Password": self.password
        }
    
    async def get_balance(self, account_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account balance from service
        
        Args:
            account_number: Optional account number, jika None akan ambil dari user login
            
        Returns:
            Response dari service
        """
        url = f"{self.base_url}/api/v1/accounts/balance"
        
        params = {}
        if account_number:
            params['account_number'] = account_number
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.config.TIMEOUT
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"Error calling service balance endpoint: {e}")
                raise
    
    async def get_customer_detail(self) -> Dict[str, Any]:
        """
        Get customer detail from service
        
        Returns:
            Response dari service dengan detail customer
        """
        url = f"{self.base_url}/api/v1/accounts/detail"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.config.TIMEOUT
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"Error calling service detail endpoint: {e}")
                raise
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login to service
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Login response dengan token/session
        """
        url = f"{self.base_url}/api/v1/auth/login"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization-Username": username,
            "Authorization-Password": password
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    timeout=self.config.TIMEOUT
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"Error calling service login endpoint: {e}")
                raise
    
    async def register(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register new user
        
        Args:
            user_data: Data registrasi user
            
        Returns:
            Registration response
        """
        url = f"{self.base_url}/api/v1/auth/register"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=user_data,
                    timeout=self.config.TIMEOUT
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"Error calling service register endpoint: {e}")
                raise


# Global instance
service_client = ServiceClient()
