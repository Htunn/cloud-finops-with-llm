"""
Main Streamlit application for the FinOps dashboard.
"""
import os
import sys
import logging
import uuid
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Generator

# Add the project root to the Python path to fix import issues
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from database.connection import get_db_session
from database.data_access import DataAccess
from utils.aws_cost_manager import AWSCostManager
from utils.azure_openai_manager import AzureOpenAIManager
from utils.local_llm_manager import LocalLLMManager
from utils.github_openai_manager import GitHubOpenAIManager
from utils.langchain_manager import LangChainManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="AWS FinOps Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Database session context manager
@contextmanager
def get_data_access() -> Generator[DataAccess, None, None]:
    """
    Context manager for data access operations.
    
    Yields:
        DataAccess object
    """
    db = next(get_db_session())
    try:
        yield DataAccess(db)
    finally:
        db.close()


# App initialization
def init_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "aws_credentials_set" not in st.session_state:
        st.session_state.aws_credentials_set = False
    
    if "preferred_llm" not in st.session_state:
        st.session_state.preferred_llm = "local"  # Default to local LLM


def display_sidebar():
    """Display the sidebar with navigation and settings."""
    st.sidebar.title("AWS FinOps Dashboard")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Cost Explorer", "Forecast", "Recommendations", "Chat Assistant", "Settings"]
    )
    
    # Authentication status
    if st.session_state.authenticated:
        st.sidebar.success(f"Authenticated: {st.session_state.user_id}")
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.rerun()
    else:
        with st.sidebar.form("login_form"):
            st.write("AWS Authentication")
            aws_access_key = st.text_input("AWS Access Key ID", type="password")
            aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                if aws_access_key and aws_secret_key:
                    # Store credentials in environment variables
                    os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key
                    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_key
                    st.session_state.aws_credentials_set = True
                    st.session_state.authenticated = True
                    st.session_state.user_id = aws_access_key[:8]  # Use part of the access key as a user ID
                    st.rerun()
                else:
                    st.error("Please enter both AWS Access Key ID and Secret Access Key")
    
    # LLM Selection
    st.sidebar.subheader("LLM Selection")
    preferred_llm = st.sidebar.radio(
        "Choose LLM for Analysis",
        ["Local (TinyLlama)", "Azure OpenAI", "GitHub OpenAI"],
        index=0 if st.session_state.preferred_llm == "local" else 
              (1 if st.session_state.preferred_llm == "azure" else 2)
    )
    
    if preferred_llm == "Local (TinyLlama)":
        st.session_state.preferred_llm = "local"
    elif preferred_llm == "Azure OpenAI":
        st.session_state.preferred_llm = "azure"
    else:
        st.session_state.preferred_llm = "github"
    
    # Date Range Selector
    st.sidebar.subheader("Date Range")
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=30)
    default_end = today
    
    if "start_date" not in st.session_state:
        st.session_state.start_date = default_start
    if "end_date" not in st.session_state:
        st.session_state.end_date = default_end
        
    start_date = st.sidebar.date_input("Start Date", st.session_state.start_date)
    end_date = st.sidebar.date_input("End Date", st.session_state.end_date)
    
    if start_date > end_date:
        st.sidebar.error("Start date must be before end date")
    else:
        st.session_state.start_date = start_date
        st.session_state.end_date = end_date
    
    # About section
    st.sidebar.markdown("---")
    st.sidebar.info(
        """
        **About**
        
        This FinOps dashboard helps you monitor and optimize your AWS cloud costs.
        
        Built with:
        - Python 3.12
        - Streamlit
        - Azure OpenAI
        - TinyLlama (Local LLM)
        - LangChain
        - PostgreSQL
        """
    )
    
    return page


def format_currency(value):
    """Format value as currency."""
    return f"${value:.2f}"


# Page functions
def display_dashboard():
    """Display the main dashboard."""
    st.title("AWS FinOps Dashboard")
    
    if not st.session_state.authenticated:
        st.warning("Please login with your AWS credentials to view the dashboard.")
        return
    
    # Initialize AWS cost manager
    aws_manager = AWSCostManager()
    
    # Get date range from session state
    start_date = st.session_state.start_date.strftime('%Y-%m-%d')
    end_date = st.session_state.end_date.strftime('%Y-%m-%d')
    
    try:
        # Load cost data
        with st.spinner("Loading AWS cost data..."):
            service_costs = aws_manager.get_cost_by_service(start_date, end_date)
            region_costs = aws_manager.get_cost_by_region(start_date, end_date)
        
        # Save to database
        with get_data_access() as data_access:
            detailed_costs = aws_manager.get_detailed_cost_data(start_date, end_date)
            # Transform data to avoid JSON serialization errors
            cost_data_entries = []
            for item in service_costs:
                # Convert dates to proper datetime objects to avoid serialization issues
                start_date_obj = datetime.datetime.strptime(item['date'] if 'date' in item else start_date, '%Y-%m-%d')
                end_date_obj = datetime.datetime.strptime(item['date'] if 'date' in item else end_date, '%Y-%m-%d')
                
                cost_data_entries.append({
                    'account_id': os.environ.get("AWS_ACCOUNT_ID", "default"),
                    'service': item['service'],
                    'region': None,
                    'usage_type': item.get('usage_type'),
                    'resource_id': None,
                    'cost': float(item['cost']),  # Ensure it's a float, not a function
                    'usage_quantity': None,
                    'start_date': start_date_obj,
                    'end_date': end_date_obj,
                    'date_range_type': 'daily',
                    'currency': item.get('currency', 'USD')
                })
            
            data_access.save_cost_data(cost_data_entries)
        
        # Create summary metrics
        if service_costs:
            total_cost = sum(item['cost'] for item in service_costs)
            top_service = max(service_costs, key=lambda x: x['cost'])
            service_count = len(service_costs)
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Cost", format_currency(total_cost))
            with col2:
                st.metric("Top Service", f"{top_service['service']} ({format_currency(top_service['cost'])})")
            with col3:
                st.metric("Services Used", str(service_count))
            
            # Create dataframes
            df_services = pd.DataFrame(service_costs)
            df_regions = pd.DataFrame(region_costs) if region_costs else None
            
            # Display service cost chart
            st.subheader("Cost by Service")
            fig_services = px.pie(
                df_services, 
                values='cost', 
                names='service',
                title=f"AWS Service Costs ({start_date} to {end_date})",
                hole=0.4
            )
            st.plotly_chart(fig_services, use_container_width=True)
            
            # Display data table
            st.subheader("Service Cost Details")
            st.dataframe(
                df_services.sort_values('cost', ascending=False),
                column_config={
                    "service": "Service",
                    "cost": st.column_config.NumberColumn("Cost", format=format_currency),
                    "currency": "Currency"
                },
                hide_index=True
            )
            
            # Display region cost chart if available
            if df_regions is not None and not df_regions.empty:
                st.subheader("Cost by Region")
                fig_regions = px.bar(
                    df_regions, 
                    x='region', 
                    y='cost',
                    title=f"AWS Region Costs ({start_date} to {end_date})"
                )
                st.plotly_chart(fig_regions, use_container_width=True)
            
            # Get cost forecast
            with st.expander("Cost Forecast Preview"):
                try:
                    forecast = aws_manager.get_cost_forecast()
                    if forecast:
                        st.subheader("Cost Forecast for Next 30 Days")
                        st.write(f"Forecasted Cost: {format_currency(forecast['mean_forecast'])}")
                        
                        # Create forecast dataframe
                        df_forecast = pd.DataFrame(forecast['forecasted_values'])
                        fig_forecast = px.line(
                            df_forecast,
                            x='date',
                            y='amount',
                            title="Cost Forecast Trend"
                        )
                        st.plotly_chart(fig_forecast, use_container_width=True)
                except Exception as e:
                    st.warning(f"Unable to load forecast: {str(e)}")
        else:
            st.info("No cost data available for the selected date range.")
    
    except Exception as e:
        st.error(f"Error loading AWS cost data: {str(e)}")
        st.error("Please check your AWS credentials and try again.")


def display_cost_explorer():
    """Display detailed cost explorer."""
    st.title("Cost Explorer")
    
    if not st.session_state.authenticated:
        st.warning("Please login with your AWS credentials to use the Cost Explorer.")
        return
    
    # Initialize AWS cost manager
    aws_manager = AWSCostManager()
    
    # Get date range from session state
    start_date = st.session_state.start_date.strftime('%Y-%m-%d')
    end_date = st.session_state.end_date.strftime('%Y-%m-%d')
    
    # Add granularity selection
    granularity = st.radio(
        "Time Granularity",
        ["Daily", "Monthly"],
        horizontal=True
    )
    
    # Add grouping options
    grouping = st.multiselect(
        "Group By",
        ["Service", "Region", "Usage Type"],
        default=["Service"]
    )
    
    try:
        # Load detailed cost data
        with st.spinner("Loading detailed cost data..."):
            detailed_costs = aws_manager.get_detailed_cost_data(
                start_date, 
                end_date,
                granularity=granularity.upper()
            )
        
        if detailed_costs:
            # Create dataframe
            df = pd.DataFrame(detailed_costs)
            
            # Apply filters
            st.subheader("Filters")
            col1, col2 = st.columns(2)
            
            with col1:
                if 'service' in df.columns:
                    services = ["All"] + sorted(df['service'].unique().tolist())
                    selected_service = st.selectbox("Service", services)
                    if selected_service != "All":
                        df = df[df['service'] == selected_service]
            
            with col2:
                if 'usage_type' in df.columns:
                    usage_types = ["All"] + sorted(df['usage_type'].unique().tolist())
                    selected_usage = st.selectbox("Usage Type", usage_types)
                    if selected_usage != "All":
                        df = df[df['usage_type'] == selected_usage]
            
            # Display charts
            st.subheader("Cost Analysis")
            
            # Time series chart
            if 'start_date' in df.columns:
                df['date'] = pd.to_datetime(df['start_date'])
                time_series = df.groupby('date')['cost'].sum().reset_index()
                
                fig = px.line(
                    time_series,
                    x='date',
                    y='cost',
                    title="Cost Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Group by charts
            if grouping:
                for group in grouping:
                    group_col = group.lower().replace(" ", "_")
                    
                    if group_col in df.columns or (group_col == "service" and "service" in df.columns):
                        actual_col = "service" if group_col == "service" else group_col
                        grouped_data = df.groupby(actual_col)['cost'].sum().reset_index()
                        grouped_data = grouped_data.sort_values('cost', ascending=False).head(10)
                        
                        fig = px.bar(
                            grouped_data,
                            x=actual_col,
                            y='cost',
                            title=f"Top 10 Costs by {group}"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Display data table
            st.subheader("Detailed Cost Data")
            st.dataframe(
                df,
                column_config={
                    "cost": st.column_config.NumberColumn("Cost", format="$%.2f"),
                    "usage_quantity": st.column_config.NumberColumn("Usage Quantity"),
                    "start_date": "Start Date",
                    "end_date": "End Date"
                }
            )
            
            # Export options
            st.download_button(
                label="Export as CSV",
                data=df.to_csv().encode('utf-8'),
                file_name=f"aws_costs_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("No cost data available for the selected date range.")
    
    except Exception as e:
        st.error(f"Error in Cost Explorer: {str(e)}")


def display_forecast():
    """Display cost forecasting."""
    st.title("Cost Forecasting")
    
    if not st.session_state.authenticated:
        st.warning("Please login with your AWS credentials to view forecasts.")
        return
    
    # Initialize managers
    aws_manager = AWSCostManager()
    
    col1, col2 = st.columns(2)
    
    with col1:
        forecast_days = st.slider("Forecast Days", min_value=7, max_value=90, value=30)
    
    with col2:
        forecast_method = st.radio(
            "Forecast Method",
            ["AWS Cost Explorer", "AI-Based (LLM)"],
            horizontal=True
        )
    
    # Get built-in AWS forecast
    try:
        with st.spinner("Generating forecast..."):
            if forecast_method == "AWS Cost Explorer":
                # Get AWS Cost Explorer forecast
                forecast = aws_manager.get_cost_forecast(days=forecast_days)
                
                if forecast:
                    st.subheader(f"AWS Cost Explorer Forecast (Next {forecast_days} Days)")
                    
                    # Calculate metrics
                    forecast_total = forecast['mean_forecast']
                    
                    # Get historical data for comparison
                    start_date = (datetime.date.today() - datetime.timedelta(days=forecast_days)).strftime('%Y-%m-%d')
                    end_date = datetime.date.today().strftime('%Y-%m-%d')
                    historical = aws_manager.get_cost_by_service(start_date, end_date)
                    historical_total = sum(item['cost'] for item in historical) if historical else 0
                    
                    change_pct = ((forecast_total - historical_total) / historical_total * 100) if historical_total > 0 else 0
                    
                    # Display metrics
                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                    with metrics_col1:
                        st.metric(
                            "Forecasted Total Cost", 
                            format_currency(forecast_total),
                            f"{change_pct:.1f}%" if historical_total > 0 else None
                        )
                    with metrics_col2:
                        st.metric("Previous Period Cost", format_currency(historical_total))
                    with metrics_col3:
                        daily_avg = forecast_total / forecast_days
                        st.metric("Daily Average", format_currency(daily_avg))
                    
                    # Plot forecast values
                    if 'forecasted_values' in forecast:
                        df_forecast = pd.DataFrame(forecast['forecasted_values'])
                        df_forecast['date'] = pd.to_datetime(df_forecast['date'])
                        
                        fig = px.line(
                            df_forecast,
                            x='date',
                            y='amount',
                            title="Cost Forecast Trend"
                        )
                        
                        # Add historical data if available
                        if historical:
                            # Create a dataframe from historical data
                            historical_dates = []
                            historical_costs = []
                            
                            # Group historical data by date
                            historical_by_date = {}
                            for item in historical:
                                date = item.get('date', start_date)
                                if date not in historical_by_date:
                                    historical_by_date[date] = 0
                                historical_by_date[date] += item['cost']
                            
                            for date, cost in historical_by_date.items():
                                historical_dates.append(date)
                                historical_costs.append(cost)
                            
                            df_historical = pd.DataFrame({
                                'date': historical_dates,
                                'amount': historical_costs
                            })
                            df_historical['date'] = pd.to_datetime(df_historical['date'])
                            
                            # Add trace for historical data
                            fig.add_trace(
                                go.Scatter(
                                    x=df_historical['date'],
                                    y=df_historical['amount'],
                                    mode='lines',
                                    name='Historical',
                                    line=dict(color='gray', dash='dash')
                                )
                            )
                        
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No forecast data available from AWS Cost Explorer.")
            
            else:  # AI-Based Forecast
                # Use LangChain manager for AI forecast
                langchain_manager = LangChainManager()
                
                # Get historical cost data from database
                with get_data_access() as data_access:
                    start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')
                    end_date = datetime.date.today().strftime('%Y-%m-%d')
                    historical = data_access.get_cost_by_day(
                        datetime.datetime.strptime(start_date, '%Y-%m-%d'),
                        datetime.datetime.strptime(end_date, '%Y-%m-%d')
                    )
                
                if historical:
                    st.subheader(f"AI-Generated Cost Forecast (Next {forecast_days} Days)")
                    
                    # Generate forecast with LangChain
                    forecast_text = langchain_manager.generate_cost_forecast()
                    
                    # Display the AI-generated forecast
                    st.markdown(forecast_text)
                else:
                    st.warning("No historical data available for AI-based forecasting. Please generate some historical data first.")
    
    except Exception as e:
        st.error(f"Error generating forecast: {str(e)}")


def display_recommendations():
    """Display cost optimization recommendations."""
    st.title("Cost Optimization Recommendations")
    
    if not st.session_state.authenticated:
        st.warning("Please login with your AWS credentials to view recommendations.")
        return
    
    # Initialize managers
    aws_manager = AWSCostManager()
    
    # Recommendation source
    recommendation_source = st.radio(
        "Recommendation Source",
        ["AWS Generated", "AI Generated (LLM)"],
        horizontal=True
    )
    
    try:
        with st.spinner("Loading recommendations..."):
            if recommendation_source == "AWS Generated":
                # Get AWS recommendations
                recommendations = aws_manager.get_cost_optimization_recommendations()
                
                if recommendations:
                    # Calculate potential savings
                    total_savings = sum(rec.get('potential_savings', 0) for rec in recommendations)
                    
                    st.metric("Total Potential Savings", format_currency(total_savings))
                    
                    # Display recommendations
                    for i, rec in enumerate(recommendations):
                        with st.expander(f"{rec['service']} - {rec['recommendation_type']} (Save {format_currency(rec['potential_savings'])})"):
                            st.write(f"**Resource:** {rec.get('resourceId', 'N/A')}")
                            st.write(f"**Description:** {rec['description']}")
                            st.write(f"**Potential Savings:** {format_currency(rec['potential_savings'])}")
                            
                            # Action buttons (simulated)
                            col1, col2 = st.columns(2)
                            with col1:
                                st.button(f"Implement_{i}", label="Implement")
                            with col2:
                                st.button(f"Dismiss_{i}", label="Dismiss")
                else:
                    st.info("No recommendations available from AWS.")
            
            else:  # AI Generated
                # Initialize the appropriate LLM manager based on user preference
                if st.session_state.preferred_llm == "local":
                    llm_manager = LocalLLMManager()
                elif st.session_state.preferred_llm == "azure":
                    llm_manager = AzureOpenAIManager()
                else:  # GitHub OpenAI
                    llm_manager = GitHubOpenAIManager()
                
                # Get cost data
                start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
                end_date = datetime.date.today().strftime('%Y-%m-%d')
                cost_data = aws_manager.get_detailed_cost_data(start_date, end_date)
                
                if cost_data:
                    # Generate recommendations with LLM
                    if st.session_state.preferred_llm == "azure":
                        recommendations = llm_manager.generate_cost_recommendations(cost_data)
                    else:
                        # For local LLM, generate text recommendations
                        insights = llm_manager.generate_cost_insights(cost_data)
                        st.markdown(insights)
                        
                        # Simulated structured recommendations for local LLM
                        recommendations = [
                            {
                                "resource_id": "i-1234567890abcdef0",
                                "service_name": "Amazon EC2",
                                "recommendation_type": "Right Size",
                                "description": "EC2 instance is underutilized. Consider downsizing to a smaller instance type.",
                                "potential_savings": 25.0
                            },
                            {
                                "resource_id": "s3-bucket-name",
                                "service_name": "Amazon S3",
                                "recommendation_type": "Storage Class Change",
                                "description": "Consider moving infrequently accessed data to S3 Standard-IA.",
                                "potential_savings": 15.0
                            }
                        ]
                    
                    # Save recommendations to database
                    with get_data_access() as data_access:
                        account_id = os.environ.get("AWS_ACCOUNT_ID", "default")
                        for rec in recommendations:
                            rec['account_id'] = account_id
                        data_access.save_recommendations(recommendations)
                    
                    # Display recommendations
                    if recommendations:
                        total_savings = sum(rec.get('potential_savings', 0) for rec in recommendations)
                        st.metric("Total Potential Savings", format_currency(total_savings))
                        
                        for i, rec in enumerate(recommendations):
                            with st.expander(f"{rec['service_name']} - {rec['recommendation_type']} (Save {format_currency(rec['potential_savings'])})"):
                                st.write(f"**Resource:** {rec.get('resource_id', 'N/A')}")
                                st.write(f"**Description:** {rec['description']}")
                                st.write(f"**Potential Savings:** {format_currency(rec['potential_savings'])}")
                    else:
                        st.info("No AI-generated recommendations available.")
                else:
                    st.warning("No cost data available for analysis. Please check your AWS credentials and data range.")
    
    except Exception as e:
        st.error(f"Error loading recommendations: {str(e)}")


def display_chat_assistant():
    """Display chat assistant for cost analysis queries."""
    st.title("FinOps Chat Assistant")
    
    if not st.session_state.authenticated:
        st.warning("Please login with your AWS credentials to use the chat assistant.")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    prompt = st.chat_input("Ask about your AWS costs...")
    
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Initialize the appropriate LLM manager based on user preference
        try:
            # Get response from LLM
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Get cost data for context (needed for all LLMs)
                    aws_manager = AWSCostManager()
                    start_date = st.session_state.start_date.strftime('%Y-%m-%d')
                    end_date = st.session_state.end_date.strftime('%Y-%m-%d')
                    cost_data = aws_manager.get_cost_by_service(start_date, end_date)
                    
                    if st.session_state.preferred_llm == "local":
                        # Use local LLM (TinyLlama)
                        llm_manager = LocalLLMManager()
                        response = llm_manager.analyze_cost_data(cost_data, prompt)
                        llm_model = "TinyLlama"
                        tokens_used = None
                    elif st.session_state.preferred_llm == "github":
                        try:
                            # Use GitHub OpenAI
                            github_manager = GitHubOpenAIManager()
                            response = github_manager.analyze_cost_data(cost_data, prompt)
                            llm_model = "GitHub OpenAI"
                            tokens_used = None
                            
                            # If we got an error response, display it nicely
                            if "Error" in response or "Access denied" in response:
                                st.error(response)
                        except ImportError:
                            st.error("GitHub OpenAI integration requires the 'openai' package. Please install it with: pip install openai>=1.12.0")
                            response = "Error: Required packages not installed."
                            llm_model = "Error"
                            tokens_used = None
                    else:
                        # Use Azure OpenAI
                        azure_manager = AzureOpenAIManager()
                        
                        # Get cost data for context
                        aws_manager = AWSCostManager()
                        start_date = st.session_state.start_date.strftime('%Y-%m-%d')
                        end_date = st.session_state.end_date.strftime('%Y-%m-%d')
                        cost_data = aws_manager.get_cost_by_service(start_date, end_date)
                        
                        # Generate response
                        response = azure_manager.generate_cost_analysis(cost_data, prompt)
                        llm_model = "Azure OpenAI"
                        tokens_used = None  # In a real app, you'd extract this from the response
                    
                    # Display the response
                    st.markdown(response)
                    
                    # Save to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Save to database
                    with get_data_access() as data_access:
                        data_access.save_chat_history(
                            session_id=st.session_state.session_id,
                            user_query=prompt,
                            assistant_response=response,
                            llm_model=llm_model,
                            tokens_used=tokens_used
                        )
        
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {str(e)}"})


def display_settings():
    """Display settings page."""
    st.title("Settings")
    
    if not st.session_state.authenticated:
        st.warning("Please login to access settings.")
        return
    
    st.subheader("AWS Settings")
    
    # AWS Region Setting
    aws_regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-central-1",
        "ap-northeast-1", "ap-southeast-1", "ap-southeast-2"
    ]
    
    current_region = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")
    region = st.selectbox("AWS Region", aws_regions, index=aws_regions.index(current_region))
    
    if st.button("Save AWS Region"):
        os.environ["AWS_DEFAULT_REGION"] = region
        st.success(f"AWS region updated to {region}")
    
    st.subheader("LLM Settings")
    
    # Azure OpenAI Settings
    st.write("Azure OpenAI Configuration")
    
    azure_api_key = st.text_input("Azure OpenAI API Key", type="password")
    azure_endpoint = st.text_input("Azure OpenAI Endpoint")
    azure_deployment = st.text_input("Azure OpenAI Deployment Name")
    
    if st.button("Save Azure OpenAI Settings"):
        if all([azure_api_key, azure_endpoint, azure_deployment]):
            os.environ["AZURE_OPENAI_API_KEY"] = azure_api_key
            os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint
            os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = azure_deployment
            st.success("Azure OpenAI settings updated")
        else:
            st.error("All Azure OpenAI fields are required")
    
    # Local LLM Settings
    st.write("Local LLM (TinyLlama) Configuration")
    
    use_gpu = st.checkbox("Use M3 GPU Acceleration", value=True)
    
    if st.button("Save Local LLM Settings"):
        os.environ["LOCAL_LLM_USE_GPU"] = str(use_gpu).lower()
        st.success("Local LLM settings updated")
        
    # GitHub OpenAI Settings
    st.write("GitHub OpenAI Configuration")
    
    github_token = st.text_input("GitHub Token", type="password")
    github_endpoint = st.text_input("GitHub OpenAI Endpoint", value="https://models.github.ai/inference")
    github_model = st.text_input("GitHub OpenAI Model", value="openai/gpt-4.1")
    
    if st.button("Save GitHub OpenAI Settings"):
        if github_token:
            os.environ["GITHUB_TOKEN"] = github_token
            os.environ["GITHUB_OPENAI_ENDPOINT"] = github_endpoint
            os.environ["GITHUB_OPENAI_MODEL"] = github_model
            st.success("GitHub OpenAI settings updated")
        else:
            st.error("GitHub Token is required")
    
    # User Preferences
    st.subheader("User Preferences")
    
    # Load user settings if available
    user_settings = None
    if st.session_state.user_id:
        with get_data_access() as data_access:
            user_settings = data_access.get_user_settings(st.session_state.user_id)
    
    # Default LLM preference
    default_llm = "local"
    if user_settings and user_settings.get('preferred_llm'):
        default_llm = user_settings.get('preferred_llm')
    
    preferred_llm = st.radio(
        "Default LLM",
        ["local", "azure", "github"],
        index=0 if default_llm == "local" else (1 if default_llm == "azure" else 2)
    )
    
    # Budget alerts
    st.write("Budget Alerts")
    enable_budget_alerts = st.checkbox("Enable Budget Alerts", value=True)
    budget_threshold = st.slider("Budget Alert Threshold ($)", 0, 1000, 100)
    
    if st.button("Save User Preferences"):
        settings = {
            'preferred_llm': preferred_llm,
            'budget_alerts': {
                'enabled': enable_budget_alerts,
                'threshold': budget_threshold
            }
        }
        
        with get_data_access() as data_access:
            data_access.save_user_settings(st.session_state.user_id, settings)
        
        st.session_state.preferred_llm = preferred_llm
        st.success("User preferences saved")
    
    # Database connection test
    st.subheader("Database Connection")
    
    if st.button("Test Database Connection"):
        try:
            with get_data_access() as data_access:
                st.success("Database connection successful!")
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")


# Main app
def main():
    """Main application function."""
    # Initialize session state
    init_session_state()
    
    # Display sidebar and get selected page
    page = display_sidebar()
    
    # Display selected page
    if page == "Dashboard":
        display_dashboard()
    elif page == "Cost Explorer":
        display_cost_explorer()
    elif page == "Forecast":
        display_forecast()
    elif page == "Recommendations":
        display_recommendations()
    elif page == "Chat Assistant":
        display_chat_assistant()
    elif page == "Settings":
        display_settings()


if __name__ == "__main__":
    main()
