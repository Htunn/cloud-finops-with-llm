"""
Demonstration of GitHub OpenAI integration for the FinOps project.

This script shows how to use the GitHub OpenAI API for generating FinOps insights.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path to fix import issues
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.github_openai_manager import GitHubOpenAIManager
from utils.aws_cost_manager import AWSCostManager

# Load environment variables
load_dotenv()

def main():
    # Check if GitHub token is set
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GitHub token not found in environment variables.")
        print("Please set the GITHUB_TOKEN environment variable in .env file.")
        return
        
    print("GitHub OpenAI Integration Demo")
    print("------------------------------\n")
    
    # Initialize GitHub OpenAI manager
    github_manager = GitHubOpenAIManager()
    
    # Test basic prompt
    print("1. Basic FinOps Question\n")
    prompt = "What are the top 5 AWS cost optimization strategies?"
    print(f"Prompt: {prompt}\n")
    
    response = github_manager.generate_response(prompt)
    print(f"Response:\n{response}\n")
    
    # Get some AWS cost data for analysis (if AWS credentials are set)
    try:
        print("\n2. AWS Cost Data Analysis\n")
        
        # Initialize AWS cost manager
        aws_manager = AWSCostManager()
        
        # Get cost data for the last 30 days
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"Fetching AWS cost data from {start_date} to {end_date}...")
        cost_data = aws_manager.get_cost_by_service(start_date, end_date)
        
        if cost_data:
            # Analyze the cost data using GitHub OpenAI
            question = "What are the main cost drivers and how can I optimize them?"
            print(f"Question: {question}\n")
            
            analysis = github_manager.analyze_cost_data(cost_data, question)
            print(f"Analysis:\n{analysis}\n")
            
            # Generate cost insights
            print("\n3. Cost Insights Generation\n")
            insights = github_manager.generate_cost_insights(cost_data)
            print(f"Generated Insights:\n{insights}\n")
        else:
            print("No AWS cost data available. Please check your AWS credentials.")
    
    except Exception as e:
        print(f"Error accessing AWS cost data: {e}")
        print("Skipping cost data analysis demonstrations.")

if __name__ == "__main__":
    main()
