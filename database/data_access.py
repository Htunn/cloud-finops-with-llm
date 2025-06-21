"""
Data access layer for database operations.
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database.models import AWSCostData, CostForecast, CostRecommendation, ChatHistory, UserSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAccess:
    """Data access layer for database operations."""
    
    def __init__(self, db_session: Session) -> None:
        """
        Initialize the data access layer.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    # AWS Cost Data operations
    
    def save_cost_data(self, cost_data: List[Dict[str, Any]]) -> None:
        """
        Save AWS cost data to the database.
        
        Args:
            cost_data: List of cost data items to save
        """
        try:
            for item in cost_data:
                cost_entry = AWSCostData(
                    account_id=item.get('account_id'),
                    service_name=item.get('service'),
                    region=item.get('region'),
                    usage_type=item.get('usage_type'),
                    resource_id=item.get('resource_id'),
                    cost=item.get('cost'),
                    usage_quantity=item.get('usage_quantity'),
                    start_date=item.get('start_date'),
                    end_date=item.get('end_date'),
                    date_range_type=item.get('date_range_type', 'daily'),
                    currency=item.get('currency', 'USD')
                )
                self.db.add(cost_entry)
            
            self.db.commit()
            logger.info(f"Saved {len(cost_data)} cost data entries to database.")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving cost data: {e}")
            raise
    
    def get_cost_by_service(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get cost data grouped by service for a date range.
        
        Args:
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            List of cost data grouped by service
        """
        try:
            results = (
                self.db.query(
                    AWSCostData.service_name,
                    func.sum(AWSCostData.cost).label('total_cost'),
                    func.min(AWSCostData.currency).label('currency')
                )
                .filter(AWSCostData.start_date >= start_date)
                .filter(AWSCostData.end_date <= end_date)
                .group_by(AWSCostData.service_name)
                .order_by(desc('total_cost'))
                .all()
            )
            
            return [
                {
                    'service': result.service_name,
                    'total_cost': float(result.total_cost),
                    'currency': result.currency
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Error retrieving cost by service: {e}")
            return []
    
    def get_cost_by_day(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get cost data grouped by day for a date range.
        
        Args:
            start_date: Start date for the query
            end_date: End date for the query
            
        Returns:
            List of cost data grouped by day
        """
        try:
            results = (
                self.db.query(
                    func.date_trunc('day', AWSCostData.start_date).label('day'),
                    func.sum(AWSCostData.cost).label('total_cost'),
                    func.min(AWSCostData.currency).label('currency')
                )
                .filter(AWSCostData.start_date >= start_date)
                .filter(AWSCostData.end_date <= end_date)
                .group_by('day')
                .order_by('day')
                .all()
            )
            
            return [
                {
                    'date': result.day.strftime('%Y-%m-%d'),
                    'total_cost': float(result.total_cost),
                    'currency': result.currency
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Error retrieving cost by day: {e}")
            return []
    
    # Cost Forecast operations
    
    def save_forecast(self, forecasts: List[Dict[str, Any]]) -> None:
        """
        Save cost forecasts to the database.
        
        Args:
            forecasts: List of forecast items to save
        """
        try:
            for item in forecasts:
                forecast_entry = CostForecast(
                    account_id=item.get('account_id'),
                    service_name=item.get('service_name'),
                    forecast_date=item.get('forecast_date'),
                    forecasted_cost=item.get('forecasted_cost'),
                    confidence_level=item.get('confidence_level'),
                    model_version=item.get('model_version')
                )
                self.db.add(forecast_entry)
            
            self.db.commit()
            logger.info(f"Saved {len(forecasts)} forecast entries to database.")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving forecasts: {e}")
            raise
    
    def get_latest_forecasts(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get the latest cost forecasts.
        
        Args:
            limit: Maximum number of forecast items to return
            
        Returns:
            List of latest forecast items
        """
        try:
            results = (
                self.db.query(CostForecast)
                .order_by(desc(CostForecast.created_at))
                .limit(limit)
                .all()
            )
            
            return [
                {
                    'account_id': result.account_id,
                    'service_name': result.service_name,
                    'forecast_date': result.forecast_date.strftime('%Y-%m-%d'),
                    'forecasted_cost': float(result.forecasted_cost),
                    'confidence_level': float(result.confidence_level) if result.confidence_level else None,
                    'model_version': result.model_version,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Error retrieving latest forecasts: {e}")
            return []
    
    # Cost Recommendations operations
    
    def save_recommendations(self, recommendations: List[Dict[str, Any]]) -> None:
        """
        Save cost optimization recommendations to the database.
        
        Args:
            recommendations: List of recommendation items to save
        """
        try:
            for item in recommendations:
                recommendation_entry = CostRecommendation(
                    account_id=item.get('account_id'),
                    resource_id=item.get('resource_id'),
                    service_name=item.get('service_name'),
                    recommendation_type=item.get('recommendation_type'),
                    description=item.get('description'),
                    potential_savings=item.get('potential_savings'),
                    status=item.get('status', 'open')
                )
                self.db.add(recommendation_entry)
            
            self.db.commit()
            logger.info(f"Saved {len(recommendations)} recommendation entries to database.")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving recommendations: {e}")
            raise
    
    def get_open_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get open cost optimization recommendations.
        
        Returns:
            List of open recommendation items
        """
        try:
            results = (
                self.db.query(CostRecommendation)
                .filter(CostRecommendation.status == 'open')
                .order_by(desc(CostRecommendation.potential_savings))
                .all()
            )
            
            return [
                {
                    'id': str(result.id),
                    'account_id': result.account_id,
                    'resource_id': result.resource_id,
                    'service_name': result.service_name,
                    'recommendation_type': result.recommendation_type,
                    'description': result.description,
                    'potential_savings': float(result.potential_savings) if result.potential_savings else None,
                    'status': result.status,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Error retrieving open recommendations: {e}")
            return []
    
    # Chat History operations
    
    def save_chat_history(self, session_id: str, user_query: str, assistant_response: str, llm_model: str = None, tokens_used: int = None) -> None:
        """
        Save chat history to the database.
        
        Args:
            session_id: Chat session ID
            user_query: User's query text
            assistant_response: Assistant's response text
            llm_model: LLM model used
            tokens_used: Number of tokens used
        """
        try:
            session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
            
            chat_entry = ChatHistory(
                session_id=session_uuid,
                user_query=user_query,
                assistant_response=assistant_response,
                llm_model=llm_model,
                tokens_used=tokens_used
            )
            self.db.add(chat_entry)
            self.db.commit()
            logger.info(f"Saved chat history for session {session_id}.")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving chat history: {e}")
            raise
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Chat session ID
            limit: Maximum number of history items to return
            
        Returns:
            List of chat history items
        """
        try:
            session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
            
            results = (
                self.db.query(ChatHistory)
                .filter(ChatHistory.session_id == session_uuid)
                .order_by(desc(ChatHistory.created_at))
                .limit(limit)
                .all()
            )
            
            return [
                {
                    'id': str(result.id),
                    'session_id': str(result.session_id),
                    'user_query': result.user_query,
                    'assistant_response': result.assistant_response,
                    'llm_model': result.llm_model,
                    'tokens_used': result.tokens_used,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                for result in results
            ]
        
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []
    
    # User Settings operations
    
    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get user settings.
        
        Args:
            user_id: User ID
            
        Returns:
            User settings
        """
        try:
            result = (
                self.db.query(UserSettings)
                .filter(UserSettings.user_id == user_id)
                .first()
            )
            
            if result:
                return {
                    'id': str(result.id),
                    'user_id': result.user_id,
                    'preferred_llm': result.preferred_llm,
                    'budget_alerts': result.budget_alerts,
                    'custom_dashboards': result.custom_dashboards,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': result.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving user settings: {e}")
            return None
    
    def save_user_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        """
        Save user settings.
        
        Args:
            user_id: User ID
            settings: Settings to save
        """
        try:
            existing_settings = (
                self.db.query(UserSettings)
                .filter(UserSettings.user_id == user_id)
                .first()
            )
            
            if existing_settings:
                # Update existing settings
                for key, value in settings.items():
                    if hasattr(existing_settings, key):
                        setattr(existing_settings, key, value)
                existing_settings.updated_at = datetime.now()
            else:
                # Create new settings
                user_settings = UserSettings(
                    user_id=user_id,
                    preferred_llm=settings.get('preferred_llm', 'local'),
                    budget_alerts=settings.get('budget_alerts'),
                    custom_dashboards=settings.get('custom_dashboards')
                )
                self.db.add(user_settings)
            
            self.db.commit()
            logger.info(f"Saved settings for user {user_id}.")
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving user settings: {e}")
            raise
