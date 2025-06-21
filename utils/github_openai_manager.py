"""
GitHub OpenAI integration module for the FinOps project.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubOpenAIManager:
    """Class to manage GitHub OpenAI model interactions."""

    def __init__(self) -> None:
        """Initialize GitHub OpenAI client."""
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.endpoint = os.getenv("GITHUB_OPENAI_ENDPOINT", "https://models.github.ai/inference")
        
        # Default to models that are more likely to be accessible
        # Users can override via .env or settings page
        self.model = os.getenv("GITHUB_OPENAI_MODEL", "openai/gpt-4.1")
        
        if not self.github_token:
            logger.warning("GitHub token not found. Please set GITHUB_TOKEN environment variable.")
            self.client = None
            return
            
        try:
            self.client = OpenAI(
                base_url=self.endpoint,
                api_key=self.github_token,
            )
            logger.info(f"GitHub OpenAI client initialized with model: {self.model}")
            
            # Optional: We could add a simple model validation check here
            # But we'll assume the model is valid to avoid extra API calls
            
        except Exception as e:
            self.client = None
            if "authentication" in str(e).lower() or "401" in str(e):
                logger.error(f"Authentication error with GitHub OpenAI: Invalid token")
            else:
                logger.error(f"Error initializing GitHub OpenAI client: {e}")
                
            # If we fail to initialize, we'll return error messages when generate_response is called
    
    def generate_response(self, prompt: str, max_length: int = 1000) -> str:
        """
        Generate a response from GitHub OpenAI.
        
        Args:
            prompt: Input prompt text
            max_length: Maximum length of the generated response
            
        Returns:
            Generated response text
        """
        if not self.client:
            error_msg = "GitHub OpenAI client not initialized. Check GITHUB_TOKEN environment variable."
            logger.error(error_msg)
            return error_msg
            
        try:
            # Create a completion
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a FinOps AI assistant specialized in AWS cost analysis and optimization.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.7,
                max_tokens=max_length,
                model=self.model
            )
            
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Error generating response with GitHub OpenAI: {e}"
            logger.error(error_msg)
            
            # Provide more helpful error message for common issues
            error_str = str(e).lower()
            if "no access" in error_str or "403" in error_str:
                return f"Access denied to GitHub OpenAI model '{self.model}'. Please check your GitHub token permissions and ensure you have access to this model."
            elif "not found" in error_str or "404" in error_str:
                return f"Model '{self.model}' not found. Please check the model name in your configuration."
            elif "rate limit" in error_str or "429" in error_str:
                return "Rate limit exceeded for GitHub OpenAI API. Please try again later."
            else:
                return f"Error using GitHub OpenAI: {e}"
    
    def analyze_cost_data(self, cost_data: List[Dict[str, Any]], query: str) -> str:
        """
        Analyze cost data using GitHub OpenAI.
        
        Args:
            cost_data: Cost data to analyze
            query: User query about the cost data
            
        Returns:
            Analysis text
        """
        try:
            # Format cost data for the prompt
            cost_data_str = '\n'.join([str(item) for item in cost_data[:10]])
            if len(cost_data) > 10:
                cost_data_str += f"\n... and {len(cost_data) - 10} more items"
            
            prompt = f"""You are a FinOps AI assistant. I need you to analyze this AWS cost data and answer my question.

Here is my AWS cost data:
{cost_data_str}

My question is: {query}

Please provide a detailed analysis based on this data."""
            
            return self.generate_response(prompt, max_length=1500)
        
        except Exception as e:
            logger.error(f"Error analyzing cost data with GitHub OpenAI: {e}")
            return f"Error analyzing cost data: {str(e)}"
    
    def generate_cost_insights(self, cost_data: List[Dict[str, Any]]) -> str:
        """
        Generate cost insights using GitHub OpenAI.
        
        Args:
            cost_data: Cost data to analyze
            
        Returns:
            Cost insights text
        """
        try:
            # Format cost data for the prompt
            cost_data_str = '\n'.join([str(item) for item in cost_data[:15]])
            if len(cost_data) > 15:
                cost_data_str += f"\n... and {len(cost_data) - 15} more items"
            
            prompt = f"""You are a FinOps AI assistant. Analyze the following AWS cost data and provide insights.

AWS Cost Data:
{cost_data_str}

Please provide:
1. A summary of the current cost situation
2. Notable trends or patterns
3. Any services that seem to be costing more than expected
4. Potential areas for optimization

Format your response as a clear analysis."""
            
            return self.generate_response(prompt, max_length=2000)
        
        except Exception as e:
            logger.error(f"Error generating cost insights with GitHub OpenAI: {e}")
            return f"Error generating cost insights: {str(e)}"
