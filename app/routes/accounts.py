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

class AccountCreateRequest(BaseModel):
    """Account creation request model"""
    full_name: str = Field(..., min_length=1, max_length=100, description="Nama lengkap nasabah")
    birth_date: str | None = Field(None, description="Tanggal lahir (format: YYYY-MM-DD)")
    address: str = Field(..., min_length=1, description="Alamat lengkap")
    nik: str = Field(..., min_length=16, max_length=20, description="Nomor Induk Kependudukan")
    phone_number: str = Field(..., min_length=10, max_length=20, description="Nomor telepon")
    email: str = Field(..., max_length=100, description="Email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username untuk login")
    password: str = Field(..., min_length=6, description="Password (hashed)")
    account_number: str = Field(..., description="Nomor rekening")
    customer_id: int | None = Field(None, description="Customer ID")
    portofolio_id: str = Field(..., min_length=1, max_length=20, description="ID Portfolio")

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
@router.post('/accounts/create')
async def account_create(request: Request, data: AccountCreateRequest, _: bool = Depends(auth_dependency)):
    """
    Create new customer account in core bank
    
    This endpoint initiates account creation in the core banking system.
    Requires authentication.
    
    Request body:
    - full_name: Nama lengkap nasabah
    - birth_date: Tanggal lahir (YYYY-MM-DD) - optional
    - address: Alamat lengkap
    - nik: Nomor Induk Kependudukan (16 digit)
    - phone_number: Nomor telepon
    - email: Email address
    - username: Username untuk login
    - password: Password (hashed)
    - account_number: Nomor rekening
    - customer_id: Customer ID - optional
    - portofolio_id: ID Portfolio
    
    Returns:
    - status: success/error
    - message: Response message
    - data: Created account data from core
    """
    logger.info(f'Account create request from {request.client.host}')
    start_time = time.time()
    
    try:
        # Prepare account data
        account_data = data.dict()
        logger.info(f'Creating account for: {account_data.get("full_name")}')
        
        # Send to core bank
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{config.CORE_URL}/api/v1/accounts/create',
                json=account_data,
                timeout=config.TIMEOUT
            )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log transaction (non-blocking)
        try:
            await transaction_logger.log_transaction(
                transaction_type='account_create',
                source_system='middleware',
                target_system='core_bank',
                endpoint='/api/v1/accounts/create',
                request_payload=account_data,
                response_payload=response.json() if response.status_code in [200, 201] else None,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
        except Exception as log_error:
            logger.warning(f'Failed to log transaction: {log_error}')
        
        # Handle response
        if response.status_code in [200, 201]:
            logger.info(f'Account created successfully for {account_data.get("full_name")}')
            response_data = response.json()
            return {
                'status': 'success',
                'message': 'Account berhasil dibuat di core banking system',
                'data': response_data
            }
        elif response.status_code == 400:
            logger.error(f'Bad request to core: {response.text}')
            raise HTTPException(
                status_code=400, 
                detail=f'Invalid account data: {response.text}'
            )
        elif response.status_code == 409:
            logger.error(f'Account already exists: {response.text}')
            raise HTTPException(
                status_code=409, 
                detail='Account already exists'
            )
        else:
            logger.error(f'Core response error: {response.status_code} - {response.text}')
            raise HTTPException(
                status_code=response.status_code, 
                detail='Failed to create account in core system'
            )
            
    except httpx.TimeoutException as e:
        logger.error(f'Timeout creating account: {e}')
        try:
            await transaction_logger.log_transaction(
                transaction_type='account_create',
                source_system='middleware',
                target_system='core_bank',
                endpoint='/api/v1/accounts/create',
                request_payload=data.dict(),
                status_code=504,
                duration_ms=int((time.time() - start_time) * 1000),
                error_message='Request timeout'
            )
        except:
            pass
        raise HTTPException(status_code=504, detail='Request timeout to core system')
    
    except httpx.ConnectError as e:
        logger.error(f'Connection error to core system: {e}')
        raise HTTPException(status_code=502, detail='Cannot connect to core system')
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f'Account create failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Failed to create account: {str(e)}')