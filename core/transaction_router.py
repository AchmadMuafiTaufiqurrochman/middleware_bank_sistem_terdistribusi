# Transaction Router - Routing logic untuk internal dan external transactions
import logging
from typing import Dict, Optional
from app.config import Config
import httpx
from core.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)

class TransactionRouter:
    """
    Router untuk menentukan ke mana transaksi harus diteruskan
    - Internal: ke Core Bank sendiri
    - External: ke Minibank lain
    """
    
    def __init__(self, config: Config):
        self.config = config
    
    def determine_routing(self, target_account: str) -> Dict:
        """
        Tentukan routing berdasarkan nomor rekening tujuan
        
        Returns:
            {
                'type': 'internal' | 'external',
                'bank_code': str,
                'url': str,
                'requires_external_call': bool
            }
        """
        # Check if internal account
        if self.config.is_internal_account(target_account):
            return {
                'type': 'internal',
                'bank_code': self.config.INTERNAL_BANK_CODE,
                'url': self.config.CORE_URL,
                'requires_external_call': False
            }
        
        # External - determine bank by account prefix or routing logic
        bank_code = self._identify_external_bank(target_account)
        
        if bank_code:
            bank_config = self.config.get_external_bank_config(bank_code)
            if bank_config and bank_config.get('enabled'):
                return {
                    'type': 'external',
                    'bank_code': bank_code,
                    'url': bank_config['url'],
                    'requires_external_call': True,
                    'timeout': bank_config.get('timeout', 15),
                    'api_key': bank_config.get('api_key')
                }
        
        # Unknown bank
        return {
            'type': 'unknown',
            'bank_code': None,
            'url': None,
            'requires_external_call': False
        }
    
    def _identify_external_bank(self, account_number: str) -> Optional[str]:
        """
        Identifikasi bank external berdasarkan prefix nomor rekening
        
        Contoh logic:
        - 1234xxx = MINIBANK (internal)
        - 5678xxx = MINIBANK_A
        - 9012xxx = MINIBANK_B
        """
        # Simple prefix matching - customize based on your bank codes
        if account_number.startswith('5678'):
            return 'MINIBANK_A'
        elif account_number.startswith('9012'):
            return 'MINIBANK_B'
        
        return None
    
    async def route_transaction(self, transaction_data: Dict) -> Dict:
        """
        Route transaction to appropriate destination
        
        Args:
            transaction_data: {
                'source_account': str,
                'target_account': str,
                'amount': float,
                'description': str,
                ...
            }
        
        Returns:
            Response from target system
        """
        target_account = transaction_data.get('target_account')
        routing = self.determine_routing(target_account)
        
        logger.info(f"Routing transaction to {routing['type']} - Bank: {routing.get('bank_code')}")
        
        if routing['type'] == 'internal':
            return await self._route_internal(transaction_data)
        elif routing['type'] == 'external':
            return await self._route_external(transaction_data, routing)
        else:
            raise Exception(f"Unknown bank for account: {target_account}")
    
    async def _route_internal(self, transaction_data: Dict) -> Dict:
        """Route to internal Core Bank"""
        endpoint = f"{self.config.CORE_URL}/api/v1/transactions/internal"
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=transaction_data,
                    timeout=self.config.TIMEOUT
                )
                response.raise_for_status()
                return response.json()
        
        # Use circuit breaker
        return await circuit_breaker.call('core_bank', make_request)
    
    async def _route_external(self, transaction_data: Dict, routing: Dict) -> Dict:
        """Route to external bank"""
        bank_code = routing['bank_code']
        endpoint = f"{routing['url']}/api/v1/transactions/receive"
        
        # Transform data for external bank format
        external_data = self._transform_for_external(transaction_data, bank_code)
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                headers = {
                    'X-API-Key': routing.get('api_key', ''),
                    'Content-Type': 'application/json'
                }
                response = await client.post(
                    endpoint,
                    json=external_data,
                    headers=headers,
                    timeout=routing.get('timeout', 15)
                )
                response.raise_for_status()
                return response.json()
        
        # Use circuit breaker with bank-specific identifier
        return await circuit_breaker.call(f'external_bank_{bank_code}', make_request)
    
    def _transform_for_external(self, transaction_data: Dict, bank_code: str) -> Dict:
        """
        Transform internal transaction format to external bank format
        Sesuaikan dengan format yang diharapkan oleh external bank
        """
        return {
            'sender_bank': self.config.INTERNAL_BANK_CODE,
            'sender_account': transaction_data.get('source_account'),
            'receiver_account': transaction_data.get('target_account'),
            'amount': transaction_data.get('amount'),
            'currency': transaction_data.get('currency', 'IDR'),
            'description': transaction_data.get('description'),
            'reference_id': transaction_data.get('transaction_id'),
            'timestamp': transaction_data.get('timestamp')
        }

# Global router instance
transaction_router = TransactionRouter(Config())
