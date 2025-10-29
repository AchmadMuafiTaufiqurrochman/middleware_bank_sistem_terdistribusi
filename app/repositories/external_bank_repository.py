# app/repositories/external_bank_repository.py
"""
Repository untuk external bank status
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.external_bank_status import ExternalBankStatus, BankStatus
from typing import Optional, List
from datetime import datetime


class ExternalBankRepository:
    """
    Repository untuk CRUD operations pada external bank status
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_bank_status(self, bank_code: str) -> Optional[ExternalBankStatus]:
        """
        Get status of external bank by code
        """
        result = await self.db.execute(
            select(ExternalBankStatus)
            .where(ExternalBankStatus.bank_code == bank_code)
        )
        return result.scalar_one_or_none()
    
    async def get_all_banks(self) -> List[ExternalBankStatus]:
        """
        Get all external banks
        """
        result = await self.db.execute(
            select(ExternalBankStatus)
        )
        return result.scalars().all()
    
    async def create_or_update_status(
        self,
        bank_code: str,
        bank_name: str,
        status: BankStatus,
        error_message: Optional[str] = None
    ) -> ExternalBankStatus:
        """
        Create or update bank status
        """
        # Try to get existing
        bank = await self.get_bank_status(bank_code)
        
        if bank:
            # Update existing
            bank.status = status
            bank.last_check = datetime.utcnow()
            
            if status == BankStatus.DOWN:
                bank.failure_count += 1
                if error_message:
                    bank.last_error = error_message
            else:
                bank.failure_count = 0
                bank.last_error = None
        else:
            # Create new
            bank = ExternalBankStatus(
                bank_code=bank_code,
                bank_name=bank_name,
                status=status,
                last_check=datetime.utcnow(),
                failure_count=1 if status == BankStatus.DOWN else 0,
                last_error=error_message if status == BankStatus.DOWN else None
            )
            self.db.add(bank)
        
        await self.db.flush()
        await self.db.commit()
        return bank
    
    async def reset_failure_count(self, bank_code: str) -> bool:
        """
        Reset failure count for a bank
        """
        bank = await self.get_bank_status(bank_code)
        if bank:
            bank.failure_count = 0
            bank.status = BankStatus.ACTIVE
            bank.last_error = None
            await self.db.commit()
            return True
        return False
