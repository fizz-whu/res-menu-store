#!/usr/bin/env python3
"""
Test script to verify Lambda function detection without user interaction
"""

from lex_bot_manager import LexBotManager
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_lambda_detection():
    """Test Lambda function detection"""
    
    # Initialize the manager with debug mode
    manager = LexBotManager(debug=True)
    
    # Read bots from CSV
    bots = manager.read_bot_ids_from_csv()
    
    if not bots:
        print("No bots found in bot_ids.csv")
        return
    
    # Test with the first bot
    bot = bots[0]
    bot_id = bot['bot_id']
    region = bot['region']
    
    print(f"Testing Lambda detection for bot: {bot_id} in region: {region}")
    
    try:
        # Test AWS credentials
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"AWS User/Role: {identity['Arn']}")
        
        # Test the Lambda function detection
        components = manager.list_bot_components(bot_id, region)
        
        print(f"\nResults:")
        print(f"- Intents: {len(components['intents'])}")
        print(f"- Slots: {len(components['slots'])}")
        print(f"- Lambda Functions: {len(components['lambda_functions'])}")
        
        # Display Lambda function usage summary
        if components['lambda_functions']:
            manager.display_lambda_usage_summary(components['lambda_functions'])
        else:
            print("\nNo Lambda functions found")
            
    except NoCredentialsError:
        print("Error: AWS credentials not configured")
        print("Please run 'aws configure' or set AWS environment variables")
    except ClientError as e:
        print(f"AWS Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lambda_detection()