# app/db/models/transaction_log.py
"""
Model untuk logging semua transaksi yang melewati middleware
"""
from sqlalchemy import Column, BigInteger, String, Text, Integer, TIMESTAMP, func
from app.db.database import Base
import enum


class TransactionLog(Base):
    """
    Table untuk menyimpan audit trail semua transaksi
    """
    __tablename__ = "transaction_logs"

    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_type = Column(String(50), nullable=False)  # internal, external, inquiry
    source_system = Column(String(100))  # service, external_bank, etc.
    target_system = Column(String(100))  # core_bank, MINIBANK_A, etc.
    endpoint = Column(String(255))  # API endpoint yang dipanggil
    request_payload = Column(Text)  # JSON request
    response_payload = Column(Text)  # JSON response
    status_code = Column(Integer)  # HTTP status code
    duration_ms = Column(Integer)  # Duration in milliseconds
    error_message = Column(Text, nullable=True)  # Error message if any
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    def __repr__(self):
        return f"<TransactionLog(id={self.log_id}, type={self.transaction_type}, status={self.status_code})>"
