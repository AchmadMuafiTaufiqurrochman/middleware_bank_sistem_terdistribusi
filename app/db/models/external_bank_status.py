# app/db/models/external_bank_status.py
"""
Model untuk monitoring status external banks
"""
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, func, Text
from app.db.database import Base
import enum


class BankStatus(enum.Enum):
    """Status enum untuk external bank"""
    ACTIVE = "active"
    DOWN = "down"
    MAINTENANCE = "maintenance"


class ExternalBankStatus(Base):
    """
    Table untuk monitoring status external banks
    """
    __tablename__ = "external_bank_status"

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    bank_code = Column(String(50), unique=True, nullable=False)  # MINIBANK_A, MINIBANK_B
    bank_name = Column(String(100))
    status = Column(Enum(BankStatus), default=BankStatus.ACTIVE)
    last_check = Column(TIMESTAMP)
    failure_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    def __repr__(self):
        return f"<ExternalBankStatus(bank={self.bank_code}, status={self.status})>"
