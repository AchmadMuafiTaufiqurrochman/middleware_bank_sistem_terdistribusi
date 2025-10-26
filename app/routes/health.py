"""
Health Check and Monitoring Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import auth_dependency, get_db_connection
from app.config import Config
from core.circuit_breaker import circuit_breaker
from core.transaction_logger import transaction_logger
import logging

router = APIRouter()
config = Config()
logger = logging.getLogger(__name__)

@router.get('/health')
async def health_check():
    """
    Health check endpoint
    Returns system status, database connectivity, and circuit breaker states
    """
    try:
        conn = await get_db_connection()
        conn.close()
        
        # Get circuit breaker states
        circuit_states = {
            'core_bank': circuit_breaker.get_state('core_bank').value,
        }
        
        # Add external banks
        for bank_code in config.EXTERNAL_BANKS.keys():
            circuit_states[f'external_bank_{bank_code}'] = circuit_breaker.get_state(f'external_bank_{bank_code}').value
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'core_url': config.CORE_URL,
            'rate_limit': config.RATE_LIMIT,
            'circuit_breakers': circuit_states,
            'external_banks': {
                code: {'enabled': cfg['enabled'], 'url': cfg['url']} 
                for code, cfg in config.EXTERNAL_BANKS.items()
            }
        }
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/api/v1/stats')
async def get_statistics(_: bool = Depends(auth_dependency)):
    """
    Get transaction statistics
    Requires authentication
    """
    try:
        stats = await transaction_logger.get_transaction_stats(hours=24)
        return {
            'status': 'success',
            'period': '24 hours',
            'statistics': stats
        }
    except Exception as e:
        logger.error(f'Failed to get statistics: {e}')
        raise HTTPException(status_code=500, detail='Failed to retrieve statistics')

@router.post('/api/v1/circuit-breaker/reset/{service_name}')
async def reset_circuit_breaker(service_name: str, _: bool = Depends(auth_dependency)):
    """
    Manually reset circuit breaker for a service
    Requires authentication
    """
    try:
        circuit_breaker.reset(service_name)
        logger.info(f'Circuit breaker reset for {service_name}')
        return {
            'status': 'success',
            'message': f'Circuit breaker reset for {service_name}',
            'state': circuit_breaker.get_state(service_name).value
        }
    except Exception as e:
        logger.error(f'Failed to reset circuit breaker: {e}')
        raise HTTPException(status_code=500, detail=str(e))
