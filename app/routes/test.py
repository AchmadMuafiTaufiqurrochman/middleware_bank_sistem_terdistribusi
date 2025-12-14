"""
Test Endpoints for Service Integration Testing
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


class TestDataRequest(BaseModel):
    """Model for test data received from services"""
    service_name: Optional[str] = None
    transaction_id: Optional[str] = None
    account_number: Optional[str] = None
    amount: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@router.post('/api/v1/test/receive')
async def receive_test_data(request_data: TestDataRequest):
    """
    Test endpoint to receive data from services via HTTP POST
    
    This endpoint accepts any JSON data structure and logs it for testing purposes.
    Useful for testing service-to-service communication.
    
    Example request:
    ```json
    {
        "service_name": "bank_service",
        "transaction_id": "TXN123456",
        "account_number": "1234567890",
        "amount": 100000,
        "data": {
            "custom_field": "value"
        },
        "message": "Test transaction"
    }
    ```
    """
    try:
        # Log the received data
        logger.info(f'Test endpoint received data: {request_data.model_dump()}')
        
        response = {
            'status': 'success',
            'message': 'Data received successfully',
            'timestamp': datetime.now().isoformat(),
            'received_data': request_data.model_dump(exclude_none=True)
        }
        
        logger.info(f'Test endpoint response: {response}')
        return response
        
    except Exception as e:
        logger.error(f'Error in test endpoint: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'Failed to process test data: {str(e)}'
        )


@router.post('/api/v1/test/webhook')
async def webhook_test(request: Request):
    """
    Generic webhook test endpoint
    
    Accepts any JSON payload and returns it back with metadata.
    Useful for testing webhook integrations.
    """
    try:
        # Get the raw JSON body
        body = await request.json()
        
        # Log the webhook data
        logger.info(f'Webhook received: {body}')
        
        return {
            'status': 'success',
            'message': 'Webhook received',
            'timestamp': datetime.now().isoformat(),
            'payload': body,
            'headers': dict(request.headers)
        }
        
    except Exception as e:
        logger.error(f'Error in webhook endpoint: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'Failed to process webhook: {str(e)}'
        )


@router.post('/api/v1/test/echo')
async def echo_test(data: Dict[str, Any]):
    """
    Simple echo endpoint
    
    Returns exactly what was sent to it.
    Useful for basic connectivity testing.
    """
    try:
        logger.info(f'Echo endpoint received: {data}')
        
        return {
            'status': 'success',
            'echo': data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'Error in echo endpoint: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail=f'Failed to echo data: {str(e)}'
        )
