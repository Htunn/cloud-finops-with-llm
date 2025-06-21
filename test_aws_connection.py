"""
Test AWS connection and Cost Explorer API access.
"""
import os
import boto3
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

def test_aws_connection():
    print("Testing AWS Cost Explorer connection...")
    
    # Get AWS credentials
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    
    # Check if credentials are available
    if not access_key or not secret_key:
        print("❌ AWS credentials not found in environment variables.")
        return False
    
    try:
        # Initialize Cost Explorer client
        ce_client = boto3.client(
            'ce',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Get current date and a date 30 days ago
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Try to get cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        # Print result
        print("✅ AWS Cost Explorer API access successful!")
        print(f"Total Cost (last 30 days): {response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']} {response['ResultsByTime'][0]['Total']['UnblendedCost']['Unit']}")
        return True
        
    except Exception as e:
        print(f"❌ Error accessing AWS Cost Explorer API: {str(e)}")
        return False

if __name__ == "__main__":
    test_aws_connection()
