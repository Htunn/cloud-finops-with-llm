"""
Azure OpenAI integration module.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import AzureOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AzureOpenAIManager:
    """Class to manage Azure OpenAI API interactions."""
    
    def __init__(self) -> None:
        """Initialize Azure OpenAI client with credentials from environment variables."""
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
        
        if not all([self.api_key, self.endpoint, self.deployment_name]):
            logger.error("Azure OpenAI credentials not found in environment variables.")
            raise ValueError(
                "Azure OpenAI credentials not found. Please set AZURE_OPENAI_API_KEY, "
                "AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT_NAME."
            )
        
        try:
            # Initialize Azure OpenAI client
            self.client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version
            )
            logger.info("Azure OpenAI client initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI client: {e}")
            raise
    
    def generate_cost_analysis(self, cost_data: List[Dict[str, Any]], query: str) -> str:
        """
        Generate cost analysis using Azure OpenAI based on cost data and user query.
        
        Args:
            cost_data: Cost data for analysis
            query: User query about the cost data
            
        Returns:
            Generated analysis text
        """
        try:
            # Format cost data for the prompt
            cost_data_str = '\n'.join([str(item) for item in cost_data[:10]])
            if len(cost_data) > 10:
                cost_data_str += f"\n... and {len(cost_data) - 10} more items"
            
            messages = [
                {"role": "system", "content": "You are a FinOps AI assistant. Analyze the provided AWS cost data and answer questions about it."},
                {"role": "user", "content": f"Here is my AWS cost data:\n{cost_data_str}\n\nMy question is: {query}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.2,
                max_tokens=1000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            analysis = response.choices[0].message.content
            tokens_used = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            logger.info(f"Generated cost analysis, used {tokens_used['total_tokens']} tokens.")
            return analysis
        
        except Exception as e:
            logger.error(f"Error generating cost analysis with Azure OpenAI: {e}")
            raise
    
    def generate_cost_recommendations(self, cost_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate cost optimization recommendations using Azure OpenAI.
        
        Args:
            cost_data: Cost data to analyze for recommendations
            
        Returns:
            List of cost optimization recommendations
        """
        try:
            # Format cost data for the prompt
            cost_data_str = '\n'.join([str(item) for item in cost_data[:20]])
            if len(cost_data) > 20:
                cost_data_str += f"\n... and {len(cost_data) - 20} more items"
            
            messages = [
                {"role": "system", "content": (
                    "You are a FinOps AI assistant specializing in AWS cost optimization. "
                    "Analyze the provided AWS cost data and generate specific cost optimization recommendations. "
                    "For each recommendation, include the following fields: "
                    "resource_id, service_name, recommendation_type, description, potential_savings."
                )},
                {"role": "user", "content": f"Here is my AWS cost data:\n{cost_data_str}\n\nGenerate cost optimization recommendations."}
            ]
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.1,
                max_tokens=1500,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            
            if "recommendations" in result:
                return result["recommendations"]
            else:
                logger.warning("No recommendations found in the response")
                return []
        
        except Exception as e:
            logger.error(f"Error generating cost recommendations with Azure OpenAI: {e}")
            return []
    
    def generate_cost_forecast(self, historical_data: List[Dict[str, Any]], days: int = 30) -> Dict[str, Any]:
        """
        Generate cost forecast using Azure OpenAI based on historical data.
        
        Args:
            historical_data: Historical cost data
            days: Number of days to forecast
            
        Returns:
            Cost forecast data
        """
        try:
            # Format historical data for the prompt
            historical_data_str = '\n'.join([str(item) for item in historical_data[:50]])
            if len(historical_data) > 50:
                historical_data_str += f"\n... and {len(historical_data) - 50} more items"
            
            messages = [
                {"role": "system", "content": (
                    "You are a FinOps AI assistant with expertise in cost forecasting. "
                    "Analyze the provided AWS historical cost data and generate a forecast "
                    "for the specified number of days. Return the forecast in JSON format."
                )},
                {"role": "user", "content": f"Here is my AWS historical cost data:\n{historical_data_str}\n\nGenerate a forecast for the next {days} days."}
            ]
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.1,
                max_tokens=1500,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "json_object"}
            )
            
            # Parse JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating cost forecast with Azure OpenAI: {e}")
            raise
