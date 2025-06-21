"""
Configuration manager for the FinOps application.
"""
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the FinOps application."""
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    # PostgreSQL Configuration
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "finops")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Local LLM Configuration
    LOCAL_LLM_MODEL_PATH = os.getenv("LOCAL_LLM_MODEL_PATH", "microsoft/Phi-4-mini-4k-instruct")
    LOCAL_LLM_USE_GPU = os.getenv("LOCAL_LLM_USE_GPU", "true").lower() == "true"
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate_aws_config(cls) -> bool:
        """
        Validate AWS configuration.
        
        Returns:
            True if valid, False otherwise
        """
        if not all([cls.AWS_ACCESS_KEY_ID, cls.AWS_SECRET_ACCESS_KEY]):
            logger.warning("AWS credentials not found. Some features may not work.")
            return False
        return True
    
    @classmethod
    def validate_azure_openai_config(cls) -> bool:
        """
        Validate Azure OpenAI configuration.
        
        Returns:
            True if valid, False otherwise
        """
        if not all([cls.AZURE_OPENAI_API_KEY, cls.AZURE_OPENAI_ENDPOINT, cls.AZURE_OPENAI_DEPLOYMENT_NAME]):
            logger.warning("Azure OpenAI credentials not found. Some features may not work.")
            return False
        return True
    
    @classmethod
    def validate_postgres_config(cls) -> bool:
        """
        Validate PostgreSQL configuration.
        
        Returns:
            True if valid, False otherwise
        """
        if not all([cls.POSTGRES_USER, cls.POSTGRES_PASSWORD, cls.POSTGRES_HOST, cls.POSTGRES_PORT, cls.POSTGRES_DB]):
            logger.warning("PostgreSQL configuration not found. Database features may not work.")
            return False
        return True
