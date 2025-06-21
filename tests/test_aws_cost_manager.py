"""
Test AWS Cost Manager functionality.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.aws_cost_manager import AWSCostManager

# Load environment variables
load_dotenv()


class TestAWSCostManager(unittest.TestCase):
    """Test the AWS Cost Manager class."""
    
    @patch('utils.aws_cost_manager.boto3')
    def test_initialization(self, mock_boto3):
        """Test initialization of the AWS Cost Manager."""
        # Mock environment variables
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret"
        }):
            # Create the manager
            manager = AWSCostManager()
            
            # Check if boto3 client was created
            mock_boto3.client.assert_called_once_with(
                'ce',
                aws_access_key_id='test_key',
                aws_secret_access_key='test_secret',
                region_name=manager.region
            )
    
    @patch('utils.aws_cost_manager.boto3')
    def test_get_cost_by_service(self, mock_boto3):
        """Test get_cost_by_service method."""
        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        # Mock the response
        mock_client.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'TimePeriod': {
                        'Start': '2023-01-01',
                        'End': '2023-01-02'
                    },
                    'Groups': [
                        {
                            'Keys': ['Amazon EC2'],
                            'Metrics': {
                                'UnblendedCost': {
                                    'Amount': '10.0',
                                    'Unit': 'USD'
                                }
                            }
                        },
                        {
                            'Keys': ['Amazon S3'],
                            'Metrics': {
                                'UnblendedCost': {
                                    'Amount': '5.0',
                                    'Unit': 'USD'
                                }
                            }
                        }
                    ]
                }
            ]
        }
        
        # Create the manager with mocked environment variables
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret"
        }):
            manager = AWSCostManager()
            
            # Call the method
            result = manager.get_cost_by_service('2023-01-01', '2023-01-02')
            
            # Check the result
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['service'], 'Amazon EC2')
            self.assertEqual(result[0]['cost'], 10.0)
            self.assertEqual(result[0]['currency'], 'USD')
            self.assertEqual(result[1]['service'], 'Amazon S3')
            self.assertEqual(result[1]['cost'], 5.0)
            self.assertEqual(result[1]['currency'], 'USD')


if __name__ == '__main__':
    unittest.main()
