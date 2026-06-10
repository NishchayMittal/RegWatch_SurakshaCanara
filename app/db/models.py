from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Circular(Base):
    __tablename__ = "circulars"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    source = Column(String)
    raw_text = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    maps = relationship("MAPItem", back_populates="circular")

class MAPItem(Base):
    __tablename__ = "maps"
    id = Column(Integer, primary_key=True, index=True)
    circular_id = Column(Integer, ForeignKey("circulars.id"))
    action = Column(Text)
    confidence = Column(Float)
    assigned_department = Column(String)
    sla_days = Column(Integer)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    circular = relationship("Circular", back_populates="maps")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    event = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)