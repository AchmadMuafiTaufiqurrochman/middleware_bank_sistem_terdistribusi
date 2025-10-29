# app/db/models/service_credential.py
"""
Model untuk menyimpan credentials service layer
Dienkripsi untuk keamanan
"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func, Text
from app.db.database import Base


class ServiceCredential(Base):
    """
    Table untuk menyimpan credentials untuk service layer
    """
    __tablename__ = "service_credentials"

    credential_id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(100), unique=True, nullable=False)  # 'main_service'
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)  # Encrypted password
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    def __repr__(self):
        return f"<ServiceCredential(service={self.service_name}, active={self.is_active})>"
