# UPDATE ROUTES - accounts.py dengan service integration
"""
Account Routes - Integration dengan Service Layer
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
import logging
from app.dependencies import auth_dependency
from app.services.account_service import AccountService

router = APIRouter()
logger = logging.getLogger(__name__)

class BalanceRequest(BaseModel):
    """Balance request model"""
    account_number: Optional[str] = Field(None, min_length=10, max_length=30)

@router.get('/accounts/balance')
async def get_balance(
    request: Request,
    account_number: Optional[str] = None,
    _: bool = Depends(auth_dependency)
):
    """
    Get account balance from service
    Requires authentication
    """
    logger.info(f'Balance request from {request.client.host}')
    
    try:
        account_service = AccountService()
        result = await account_service.get_account_balance(account_number)
        return result
        
    except Exception as e:
        logger.error(f'Balance request failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/accounts/detail')
async def get_detail(
    request: Request,
    _: bool = Depends(auth_dependency)
):
    """
    Get customer account detail from service
    Requires authentication
    """
    logger.info(f'Account detail request from {request.client.host}')
    
    try:
        account_service = AccountService()
        result = await account_service.get_account_detail()
        return result
        
    except Exception as e:
        logger.error(f'Account detail request failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/accounts/sync')
async def sync_account(request: Request, _: bool = Depends(auth_dependency)):
    """
    Sync account data with service
    Deprecated: Service handles this directly now
    """
    logger.warning('Using deprecated sync endpoint')
    return {
        'status': 'deprecated',
        'message': 'This endpoint is deprecated. Use service direct API instead.'
    }
