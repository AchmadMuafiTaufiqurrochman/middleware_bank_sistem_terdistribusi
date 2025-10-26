"""
Transaction Routes - Smart Routing untuk Internal dan External Transactions
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, validator
import httpx
import time
import logging
from datetime import datetime
from app.dependencies import auth_dependency
from app.config import Config
from core.transaction_router import transaction_router
from core.transaction_logger import transaction_logger

router = APIRouter()
config = Config()
logger = logging.getLogger(__name__)

class TransactionRequest(BaseModel):
    """Transaction request model with validation"""
    source_account: str = Field(..., min_length=10, max_length=30)
    target_account: str = Field(..., min_length=10, max_length=30)
    amount: float = Field(..., gt=0)
    description: str | None = Field(None, max_length=255)
    currency: str = Field(default="IDR", max_length=3)
    
    @validator('amount')
    def validate_amount(cls, v):
        if v < config.MIN_TRANSACTION_AMOUNT:
            raise ValueError(f'Amount must be at least {config.MIN_TRANSACTION_AMOUNT}')
        if v > config.MAX_TRANSACTION_AMOUNT:
            raise ValueError(f'Amount cannot exceed {config.MAX_TRANSACTION_AMOUNT}')
        return v

class MutationRequest(BaseModel):
    """Mutation history request model"""
    account_number: str = Field(..., min_length=10, max_length=30)

@router.post('/transactions/execute')
async def transactions_execute(request: Request, data: TransactionRequest, _: bool = Depends(auth_dependency)):
    """
    Execute transaction with smart routing
    Automatically routes to internal or external bank based on account number
    Requires authentication
    """
    logger.info(f'Transaction execute request from {request.client.host}')
    start_time = time.time()
    
    try:
        # Determine routing
        routing = transaction_router.determine_routing(data.target_account)
        
        logger.info(f"Transaction routing: {routing['type']} to {routing.get('bank_code', 'unknown')}")
        
        # Add metadata to transaction
        transaction_data = data.dict()
        transaction_data['timestamp'] = datetime.now().isoformat()
        transaction_data['transaction_id'] = f"TRX{int(time.time()*1000)}"
        
        # Route transaction
        result = await transaction_router.route_transaction(transaction_data)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log transaction
        await transaction_logger.log_transaction(
            transaction_type=routing['type'],
            source_system='service',
            target_system=routing.get('bank_code', 'unknown'),
            endpoint=routing.get('url', ''),
            request_payload=transaction_data,
            response_payload=result,
            status_code=200,
            duration_ms=duration_ms
        )
        
        return {
            'status': 'success',
            'transaction_type': routing['type'],
            'bank_code': routing.get('bank_code'),
            'data': result
        }
        
    except httpx.TimeoutException:
        logger.error('Transaction request timed out')
        await transaction_logger.log_transaction(
            transaction_type='unknown',
            source_system='service',
            target_system='unknown',
            endpoint='',
            request_payload=data.dict(),
            status_code=504,
            duration_ms=int((time.time() - start_time) * 1000),
            error_message='Request timeout'
        )
        raise HTTPException(status_code=504, detail='Request timeout')
    except httpx.ConnectError:
        logger.error('Connection error to target system')
        raise HTTPException(status_code=502, detail='Connection error')
    except Exception as e:
        logger.error(f'Transaction execute failed: {e}')
        await transaction_logger.log_transaction(
            transaction_type='unknown',
            source_system='service',
            target_system='unknown',
            endpoint='',
            request_payload=data.dict(),
            status_code=500,
            duration_ms=int((time.time() - start_time) * 1000),
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/transactions/external/execute')
async def external_transactions_execute(request: Request, data: TransactionRequest, _: bool = Depends(auth_dependency)):
    """
    External transaction endpoint (deprecated)
    Use /transactions/execute instead - it has smart routing
    """
    logger.warning('Using deprecated endpoint. Use /api/v1/transactions/execute instead')
    return await transactions_execute(request, data, _)

@router.post('/history/mutations')
async def history_mutations(request: Request, data: MutationRequest, _: bool = Depends(auth_dependency)):
    """
    Get account mutation history
    Requires authentication
    """
    logger.info(f'Mutations request from {request.client.host}')
    start_time = time.time()
    
    try:
        account_number = data.account_number
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{config.CORE_URL}/api/v1/history/mutations?account_number={account_number}',
                timeout=config.TIMEOUT
            )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        await transaction_logger.log_transaction(
            transaction_type='inquiry',
            source_system='service',
            target_system='core_bank',
            endpoint='/api/v1/history/mutations',
            request_payload={'account_number': account_number},
            response_payload=response.json() if response.status_code == 200 else None,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f'Core response error: {response.status_code} - {response.text}')
            raise HTTPException(status_code=response.status_code, detail='Core system error')
            
    except httpx.TimeoutException:
        logger.error('Request to core timed out')
        raise HTTPException(status_code=504, detail='Request timeout')
    except httpx.ConnectError:
        logger.error('Connection error to core system')
        raise HTTPException(status_code=502, detail='Connection error')
    except Exception as e:
        logger.error(f'Mutations request failed: {e}')
        raise HTTPException(status_code=500, detail='Failed to fetch mutations')

@router.post('/transactions/receive')
async def receive_external_transaction(request: Request):
    """
    Receive incoming transaction from external bank
    Requires X-API-Key header from external bank
    """
    logger.info(f'Receiving external transaction from {request.client.host}')
    start_time = time.time()
    
    try:
        # Verify external bank API key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            raise HTTPException(status_code=401, detail='API Key required')
        
        # Parse request
        data = await request.json()
        
        # Transform external format to internal format
        internal_data = {
            'source_account': data.get('sender_account'),
            'target_account': data.get('receiver_account'),
            'amount': data.get('amount'),
            'description': f"Transfer from {data.get('sender_bank', 'External Bank')}: {data.get('description', '')}",
            'currency': data.get('currency', 'IDR'),
            'external_reference': data.get('reference_id'),
            'sender_bank': data.get('sender_bank')
        }
        
        # Forward to core bank
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{config.CORE_URL}/api/v1/transactions/incoming',
                json=internal_data,
                timeout=config.TIMEOUT
            )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log transaction
        await transaction_logger.log_transaction(
            transaction_type='incoming_external',
            source_system=data.get('sender_bank', 'unknown'),
            target_system='core_bank',
            endpoint='/api/v1/transactions/incoming',
            request_payload=data,
            response_payload=response.json() if response.status_code == 200 else None,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        if response.status_code == 200:
            return {
                'status': 'success',
                'message': 'Transaction processed',
                'data': response.json()
            }
        else:
            raise HTTPException(status_code=response.status_code, detail='Transaction failed')
            
    except Exception as e:
        logger.error(f'Failed to receive external transaction: {e}')
        raise HTTPException(status_code=500, detail=str(e))
