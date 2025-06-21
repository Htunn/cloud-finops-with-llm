"""
LangChain integration for database querying and chaining LLM operations.
"""
import os
import logging
import importlib.util
import contextlib
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import core components that are less likely to cause issues
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate

# Conditional imports to avoid the problematic module
if importlib.util.find_spec("langchain_openai"):
    from langchain_openai import AzureChatOpenAI
else:
    AzureChatOpenAI = None

# Set verbose logging
try:
    from langchain.globals import set_verbose
    set_verbose(True)
except ImportError:
    # Might be renamed in newer versions
    try:
        from langchain_core.globals import set_verbose
        set_verbose(True)
    except ImportError:
        print("Warning: Could not set verbose mode for LangChain")

# Import SQLDatabase utility if available
try:
    from langchain.utilities import SQLDatabase
except ImportError:
    try:
        from langchain_community.utilities import SQLDatabase
    except ImportError:
        SQLDatabase = None

# Import SQL chain components if available
try:
    from langchain.chains import create_sql_query_chain
    from langchain.chains.sql_database.prompt import PROMPT, SQL_RESPONSE_PROMPT
except ImportError:
    try:
        from langchain_community.chains import create_sql_query_chain
        from langchain_community.chains.sql_database.prompt import PROMPT, SQL_RESPONSE_PROMPT
    except ImportError:
        create_sql_query_chain = None
        PROMPT = None
        SQL_RESPONSE_PROMPT = None

# Import callback utilities if available
try:
    from langchain.callbacks import get_openai_callback
except ImportError:
    try:
        from langchain_core.callbacks import get_openai_callback
    except ImportError:
        get_openai_callback = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Try to enable verbose mode for debugging if available
if 'set_verbose' in locals():
    set_verbose(True)


class LangChainManager:
    """Class to manage LangChain integrations for the FinOps application."""
    
    def __init__(self) -> None:
        """Initialize LangChain components."""
        # Database connection details
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "pgadmin777")
        self.postgres_db = os.getenv("POSTGRES_DB", "finops")
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port = os.getenv("POSTGRES_PORT", "5432")
        
        # Azure OpenAI details
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
        
        # Initialize database connection if SQLDatabase is available
        self.db = None
        if SQLDatabase is not None:
            try:
                self.db_uri = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
                self.db = SQLDatabase.from_uri(self.db_uri)
                logger.info("SQL database connection established successfully.")
            except Exception as e:
                logger.error(f"Error initializing database connection: {e}")
                logger.info("Continuing with limited functionality.")
        else:
            logger.warning("SQLDatabase module not available. SQL-related features will be disabled.")
        
        # Initialize Azure OpenAI LLM if credentials are available
        if all([self.api_key, self.endpoint, self.deployment_name]):
            try:
                self.llm = AzureChatOpenAI(
                    openai_api_version=self.api_version,
                    azure_deployment=self.deployment_name,
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key,
                    temperature=0.1,
                )
                logger.info("Azure OpenAI LLM initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Azure OpenAI LLM: {e}")
                self.llm = None
        else:
            logger.warning("Azure OpenAI credentials not found. SQL chains will not be available.")
            self.llm = None
    
    def create_sql_chain(self) -> Any:
        """
        Create a SQL query chain using LangChain.
        
        Returns:
            SQL query chain
        """
        # Check if required components are available
        if create_sql_query_chain is None or self.db is None:
            logger.error("Required SQL components not available. Check LangChain installation.")
            raise ImportError("Required SQL components not available. Check LangChain installation.")
        
        if not self.llm:
            logger.error("Azure OpenAI LLM not initialized. Cannot create SQL chain.")
            raise ValueError("Azure OpenAI LLM not initialized.")
        
        try:
            # Create a SQL query generation chain
            sql_chain = create_sql_query_chain(self.llm, self.db)
            logger.info("SQL query chain created successfully.")
            return sql_chain
        except Exception as e:
            logger.error(f"Error creating SQL query chain: {e}")
            raise
    
    def execute_sql_query(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Generate and execute a SQL query based on natural language.
        
        Args:
            query_text: Natural language query text
            
        Returns:
            Query results
        """
        # Check if required components are available
        if create_sql_query_chain is None or self.db is None or get_openai_callback is None:
            logger.error("Required SQL or callback components not available.")
            return [{"error": "SQL functionality not available. Check LangChain installation."}]
            
        try:
            # Create SQL chain
            sql_chain = self.create_sql_chain()
            
            # Generate SQL query
            callback_fn = get_openai_callback if get_openai_callback else lambda: contextlib.nullcontext()
            with callback_fn() as cb:
                sql_query = sql_chain.invoke({"question": query_text})
                logger.info(f"SQL query generated: {sql_query}")
                logger.info(f"Tokens used: {cb.total_tokens}")
            
            # Execute the query
            result = self.db.run(sql_query)
            
            # Format the result
            import pandas as pd
            if result:
                df = pd.read_sql_query(sql_query, self.db_uri)
                records = df.to_dict('records')
                return records
            return []
        
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return []
    
    def query_and_analyze(self, query_text: str, analysis_prompt: str) -> str:
        """
        Query database and analyze results with LLM.
        
        Args:
            query_text: Natural language query for database
            analysis_prompt: Prompt for analyzing the results
            
        Returns:
            Analysis text
        """
        try:
            # Get query results
            results = self.execute_sql_query(query_text)
            
            if not results:
                return "No data found for the query."
            
            # Format results for the prompt
            results_str = '\n'.join([str(item) for item in results[:20]])
            if len(results) > 20:
                results_str += f"\n... and {len(results) - 20} more items"
            
            # Create analysis prompt
            prompt_template = f"""You are a FinOps AI assistant. Analyze the following data from our AWS cost database and answer the question.

Database query results:
{results_str}

{analysis_prompt}

Provide a clear, detailed analysis based on this data."""
            
            # Generate analysis with LLM
            with get_openai_callback() as cb:
                response = self.llm.invoke(prompt_template)
                logger.info(f"Tokens used for analysis: {cb.total_tokens}")
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error in query and analyze: {e}")
            return f"Error analyzing data: {str(e)}"
    
    def create_cost_forecast_chain(self) -> Any:
        """
        Create a chain for cost forecasting based on historical data.
        
        Returns:
            Cost forecast chain
        """
        if not self.llm:
            logger.error("Azure OpenAI LLM not initialized. Cannot create forecast chain.")
            raise ValueError("Azure OpenAI LLM not initialized.")
        
        try:
            # Define the template for retrieving historical cost data
            historical_data_query = """
            SELECT 
                account_id, 
                service_name, 
                SUM(cost) as total_cost, 
                DATE_TRUNC('day', start_date) as date
            FROM 
                finops.aws_cost_data
            WHERE 
                start_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY 
                account_id, service_name, DATE_TRUNC('day', start_date)
            ORDER BY 
                date ASC;
            """
            
            # Define the forecast prompt
            forecast_prompt_template = """
            You are a FinOps AI assistant specializing in cost forecasting.
            Analyze the following AWS cost history data and generate a forecast for the next 30 days.
            
            Historical cost data:
            {historical_data}
            
            Based on this historical data:
            1. Identify trends in the cost data
            2. Generate a forecast for each service for the next 30 days
            3. Provide an overall forecast for total AWS costs
            4. Highlight any services that show concerning cost trends
            
            Present your forecast in a clear, structured format.
            """
            
            # Define the forecast prompt
            forecast_prompt = PromptTemplate.from_template(forecast_prompt_template)
            
            # Create the chain
            def get_historical_data():
                result = self.db.run(historical_data_query)
                return result
            
            forecast_chain = (
                RunnablePassthrough.assign(historical_data=lambda _: get_historical_data())
                | forecast_prompt
                | self.llm
                | StrOutputParser()
            )
            
            logger.info("Cost forecast chain created successfully.")
            return forecast_chain
        
        except Exception as e:
            logger.error(f"Error creating cost forecast chain: {e}")
            raise
    
    def generate_cost_forecast(self) -> str:
        """
        Generate a cost forecast using the forecast chain.
        
        Returns:
            Cost forecast text
        """
        try:
            # Create forecast chain
            forecast_chain = self.create_cost_forecast_chain()
            
            # Generate forecast
            with get_openai_callback() as cb:
                forecast = forecast_chain.invoke({})
                logger.info(f"Tokens used for forecast: {cb.total_tokens}")
            
            return forecast
        
        except Exception as e:
            logger.error(f"Error generating cost forecast: {e}")
            return f"Error generating forecast: {str(e)}"
