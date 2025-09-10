# models.py
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Float, Date
from sqlalchemy.sql import func
from backend.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(32), unique=True, index=True, nullable=True)
    name = Column(String(200), nullable=True)
    language = Column(String(32), nullable=True)
    role = Column(String(32), default="user")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    channel = Column(String(32), nullable=True)
    message_text = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)
    status = Column(String(32), default="received")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class VaccinationRecord(Base):
    __tablename__ = "vaccination_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    vaccine_name = Column(String(200), nullable=True)
    scheduled_date = Column(Date, nullable=True)
    status = Column(String(32), default="scheduled")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class CHWReport(Base):
    __tablename__ = "chw_reports"
    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, nullable=True)
    district = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    report_type = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(200), nullable=True)
    severity = Column(String(32), nullable=True)
    geo_info = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class RAGSnippet(Base):
    __tablename__ = "rag_snippets"
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, nullable=False)
    source_url = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class HITLQueue(Base):
    __tablename__ = "hitl_queue"
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, nullable=False)
    assigned_to = Column(Integer, nullable=True)
    state = Column(String(32), default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
