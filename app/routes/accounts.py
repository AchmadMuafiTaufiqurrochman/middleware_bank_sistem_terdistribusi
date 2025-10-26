"""
Account Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
import httpx
import time
import logging
from app.dependencies import auth_dependency
from app.config import Config
from core.transaction_logger import transaction_logger

router = APIRouter()
config = Config()
logger = logging.getLogger(__name__)

class AccountSyncRequest(BaseModel):
    """Account synchronization request model"""
    customer_id: int | None = None
    full_name: str = Field(..., max_length=100)
    id_portofolio: str = Field(..., max_length=20)
    birth_date: str
    address: str
    NIK: str = Field(..., max_length=20)
    phone_number: str = Field(..., max_length=20)
    email: str = Field(..., max_length=100)
    PIN: int

@router.post('/accounts/sync')
async def account_sync(request: Request, data: AccountSyncRequest, _: bool = Depends(auth_dependency)):
    """
    Synchronize customer account data to core bank
    Requires authentication
    """
    logger.info(f'Account sync request from {request.client.host}')
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{config.CORE_URL}/api/v1/accounts/create',
                json=data.dict(),
                timeout=config.TIMEOUT
            )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log transaction
        await transaction_logger.log_transaction(
            transaction_type='account_sync',
            source_system='service',
            target_system='core_bank',
            endpoint='/api/v1/accounts/create',
            request_payload=data.dict(),
            response_payload=response.json() if response.status_code == 200 else None,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        if response.status_code == 200:
            logger.info('Account sync successful')
            return {
                'status': 'success',
                'message': 'Data nasabah berhasil diteruskan ke core system',
                'data': response.json()
            }
        else:
            logger.error(f'Core response error: {response.status_code} - {response.text}')
            raise HTTPException(status_code=response.status_code, detail='Core system error')
            
    except httpx.TimeoutException:
        logger.error('Request to core timed out')
        await transaction_logger.log_transaction(
            transaction_type='account_sync',
            source_system='service',
            target_system='core_bank',
            endpoint='/api/v1/accounts/create',
            request_payload=data.dict(),
            status_code=504,
            duration_ms=int((time.time() - start_time) * 1000),
            error_message='Request timeout'
        )
        raise HTTPException(status_code=504, detail='Request timeout')
    except httpx.ConnectError:
        logger.error('Connection error to core system')
        raise HTTPException(status_code=502, detail='Connection error')
    except Exception as e:
        logger.error(f'Account sync failed: {e}')
        raise HTTPException(status_code=500, detail='Sync failed')
