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

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    tasks = relationship("Task", back_populates="department")

class SLA(Base):
    __tablename__ = "slas"
    id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    circular_source = Column(String)   # 'RBI', 'SEBI', 'MCA'
    days_to_complete = Column(Integer)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    map_id = Column(Integer, ForeignKey("maps.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    due_at = Column(DateTime)
    status = Column(String, default="assigned")
    notes = Column(Text)
    department = relationship("Department", back_populates="tasks")

class HumanReviewQueue(Base):
    __tablename__ = "human_review_queue"
    id = Column(Integer, primary_key=True)
    map_id = Column(Integer, ForeignKey("maps.id"))
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)