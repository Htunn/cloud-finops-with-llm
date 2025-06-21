"""
Database models for the FinOps application.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Date, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from database.connection import Base


class AWSCostData(Base):
    """Model for AWS cost data."""
    __tablename__ = "aws_cost_data"
    __table_args__ = {"schema": "finops"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=False)
    service_name = Column(String(100), nullable=False)
    region = Column(String(50))
    usage_type = Column(String(200))
    resource_id = Column(String(200))
    cost = Column(Float, nullable=False)
    usage_quantity = Column(Float)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    date_range_type = Column(String(20), nullable=False)
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CostForecast(Base):
    """Model for cost forecasts."""
    __tablename__ = "cost_forecasts"
    __table_args__ = {"schema": "finops"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=False)
    service_name = Column(String(100), nullable=False)
    forecast_date = Column(Date, nullable=False)
    forecasted_cost = Column(Float, nullable=False)
    confidence_level = Column(Float)
    model_version = Column(String(100))
    created_at = Column(DateTime, default=func.now())


class CostRecommendation(Base):
    """Model for cost optimization recommendations."""
    __tablename__ = "cost_recommendations"
    __table_args__ = {"schema": "finops"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String(50), nullable=False)
    resource_id = Column(String(200))
    service_name = Column(String(100), nullable=False)
    recommendation_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    potential_savings = Column(Float)
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ChatHistory(Base):
    """Model for LLM chat history."""
    __tablename__ = "chat_history"
    __table_args__ = {"schema": "finops"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    user_query = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    llm_model = Column(String(100))
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=func.now())


class UserSettings(Base):
    """Model for user settings."""
    __tablename__ = "user_settings"
    __table_args__ = {"schema": "finops"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)
    preferred_llm = Column(String(50), default="local")
    budget_alerts = Column(JSONB)
    custom_dashboards = Column(JSONB)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
