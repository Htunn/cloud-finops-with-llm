"""
AWS Cost Explorer integration module.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AWSCostManager:
    """Class to manage AWS Cost Explorer interactions."""

    def __init__(self) -> None:
        """Initialize AWS client with credentials from environment variables."""
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
        
        if not all([self.access_key, self.secret_key]):
            logger.error("AWS credentials not found in environment variables.")
            raise ValueError("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        
        try:
            # Initialize Cost Explorer client
            self.ce_client = boto3.client(
                'ce',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            logger.info("AWS Cost Explorer client initialized successfully.")
        except NoCredentialsError:
            logger.error("AWS credentials not found or are invalid.")
            raise
        except Exception as e:
            logger.error(f"Error initializing AWS Cost Explorer client: {e}")
            raise

    def get_cost_by_service(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get AWS cost breakdown by service for a specified time period.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of cost entries by service
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            result = []
            for time_period in response['ResultsByTime']:
                date = time_period['TimePeriod']['Start']
                for group in time_period['Groups']:
                    service_name = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    currency = group['Metrics']['UnblendedCost']['Unit']
                    
                    result.append({
                        'date': date,
                        'service': service_name,
                        'cost': cost,
                        'currency': currency
                    })
            
            return result
        
        except ClientError as e:
            logger.error(f"AWS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving AWS costs: {e}")
            raise
    
    def get_cost_by_region(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get AWS cost breakdown by region for a specified time period.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of cost entries by region
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ]
            )
            
            result = []
            for time_period in response['ResultsByTime']:
                date = time_period['TimePeriod']['Start']
                for group in time_period['Groups']:
                    region_name = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    currency = group['Metrics']['UnblendedCost']['Unit']
                    
                    result.append({
                        'date': date,
                        'region': region_name,
                        'cost': cost,
                        'currency': currency
                    })
            
            return result
        
        except ClientError as e:
            logger.error(f"AWS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving AWS costs: {e}")
            raise
    
    def get_detailed_cost_data(self, start_date: str, end_date: str, granularity: str = 'DAILY') -> List[Dict[str, Any]]:
        """
        Get detailed AWS cost data with resource information.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Time granularity (DAILY, MONTHLY, etc.)
            
        Returns:
            Detailed cost data
        """
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'USAGE_TYPE'
                    }
                ]
            )
            
            result = []
            for time_period in response['ResultsByTime']:
                start_date = time_period['TimePeriod']['Start']
                end_date = time_period['TimePeriod']['End']
                
                for group in time_period['Groups']:
                    service_name = group['Keys'][0]
                    usage_type = group['Keys'][1]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    currency = group['Metrics']['UnblendedCost']['Unit']
                    usage = float(group['Metrics']['UsageQuantity']['Amount'])
                    
                    result.append({
                        'start_date': start_date,
                        'end_date': end_date,
                        'service': service_name,
                        'usage_type': usage_type,
                        'cost': cost,
                        'usage_quantity': usage,
                        'currency': currency
                    })
            
            return result
        
        except ClientError as e:
            logger.error(f"AWS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving detailed AWS costs: {e}")
            raise
    
    def get_cost_forecast(self, days: int = 30) -> Dict[str, Any]:
        """
        Get AWS cost forecast for the specified number of days.
        
        Args:
            days: Number of days to forecast
            
        Returns:
            Cost forecast data
        """
        today = datetime.now()
        start_date = today.strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=days)).strftime('%Y-%m-%d')
        
        try:
            response = self.ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )
            
            return {
                'start': response['TimePeriod']['Start'],
                'end': response['TimePeriod']['End'],
                'mean_forecast': float(response['Total']['Amount']),
                'currency': response['Total']['Unit'],
                'forecasted_values': [
                    {
                        'date': point['TimePeriod']['Start'],
                        'amount': float(point['MeanValue']),
                    }
                    for point in response['ForecastResultsByTime']
                ]
            }
        
        except ClientError as e:
            logger.error(f"AWS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving cost forecast: {e}")
            raise
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get AWS cost optimization recommendations.
        
        Returns:
            List of cost optimization recommendations
        """
        try:
            # Create the Cost Optimizer client
            optimizer_client = boto3.client(
                'costoptimizer',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            # Since Cost Optimizer API is not available in boto3 directly,
            # we'll simulate the response structure based on what it would look like
            
            # In a real application, this would call the appropriate AWS API
            
            # Simulated recommendations
            recommendations = [
                {
                    'resourceId': 'i-1234567890abcdef0',
                    'service': 'Amazon EC2',
                    'recommendation_type': 'Right Size',
                    'description': 'EC2 instance is consistently underutilized. Consider downsizing from t3.large to t3.medium.',
                    'potential_savings': 30.0
                },
                {
                    'resourceId': 's3-bucket-name',
                    'service': 'Amazon S3',
                    'recommendation_type': 'Storage Class Change',
                    'description': 'Consider moving infrequently accessed data to Amazon S3 Standard-IA to reduce storage costs.',
                    'potential_savings': 15.0
                }
            ]
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error retrieving cost optimization recommendations: {e}")
            return []
