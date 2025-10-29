# app/repositories/transaction_log_repository.py
"""
Repository untuk transaction logs
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models.transaction_log import TransactionLog
from typing import List, Optional
from datetime import datetime, timedelta
import json


class TransactionLogRepository:
    """
    Repository untuk CRUD operations pada transaction logs
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_log(
        self,
        transaction_type: str,
        source_system: str,
        target_system: str,
        endpoint: str,
        request_payload: dict,
        response_payload: Optional[dict] = None,
        status_code: int = 0,
        duration_ms: int = 0,
        error_message: Optional[str] = None
    ) -> TransactionLog:
        """
        Create new transaction log
        """
        log = TransactionLog(
            transaction_type=transaction_type,
            source_system=source_system,
            target_system=target_system,
            endpoint=endpoint,
            request_payload=json.dumps(request_payload) if request_payload else None,
            response_payload=json.dumps(response_payload) if response_payload else None,
            status_code=status_code,
            duration_ms=duration_ms,
            error_message=error_message
        )
        
        self.db.add(log)
        await self.db.flush()
        await self.db.commit()
        return log
    
    async def get_recent_logs(self, limit: int = 100) -> List[TransactionLog]:
        """
        Get recent transaction logs
        """
        result = await self.db.execute(
            select(TransactionLog)
            .order_by(TransactionLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_logs_by_type(
        self, 
        transaction_type: str, 
        hours: int = 24
    ) -> List[TransactionLog]:
        """
        Get logs by transaction type within specified hours
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(TransactionLog)
            .where(
                TransactionLog.transaction_type == transaction_type,
                TransactionLog.created_at >= time_threshold
            )
            .order_by(TransactionLog.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_statistics(self, hours: int = 24) -> dict:
        """
        Get transaction statistics for the last N hours
        """
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Total transactions
        total_result = await self.db.execute(
            select(func.count(TransactionLog.log_id))
            .where(TransactionLog.created_at >= time_threshold)
        )
        total_count = total_result.scalar()
        
        # Success transactions
        success_result = await self.db.execute(
            select(func.count(TransactionLog.log_id))
            .where(
                TransactionLog.created_at >= time_threshold,
                TransactionLog.status_code == 200
            )
        )
        success_count = success_result.scalar()
        
        # Average duration
        avg_duration_result = await self.db.execute(
            select(func.avg(TransactionLog.duration_ms))
            .where(TransactionLog.created_at >= time_threshold)
        )
        avg_duration = avg_duration_result.scalar() or 0
        
        # Count by type
        internal_result = await self.db.execute(
            select(func.count(TransactionLog.log_id))
            .where(
                TransactionLog.created_at >= time_threshold,
                TransactionLog.transaction_type == 'internal'
            )
        )
        internal_count = internal_result.scalar()
        
        external_result = await self.db.execute(
            select(func.count(TransactionLog.log_id))
            .where(
                TransactionLog.created_at >= time_threshold,
                TransactionLog.transaction_type == 'external'
            )
        )
        external_count = external_result.scalar()
        
        return {
            'total_transactions': total_count,
            'success_count': success_count,
            'internal_count': internal_count,
            'external_count': external_count,
            'success_rate': round((success_count / total_count * 100) if total_count > 0 else 0, 2),
            'avg_duration_ms': round(avg_duration, 2)
        }
