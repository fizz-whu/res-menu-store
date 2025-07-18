#!/usr/bin/env python3
"""
Test script to demonstrate bot export functionality
"""

from lex_bot_manager import LexBotManager
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_bot_export():
    """Test bot export functionality"""
    
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
    
    print(f"Testing bot export for bot: {bot_id} in region: {region}")
    
    try:
        # Test AWS credentials
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"AWS User/Role: {identity['Arn']}")
        
        # Test with bot export enabled
        print("\n" + "="*60)
        print("TESTING WITH BOT EXPORT ENABLED")
        print("="*60)
        
        components = manager.list_bot_components(bot_id, region, export_bot=True)
        
        print(f"\nResults with bot export:")
        print(f"- Intents: {len(components['intents'])}")
        print(f"- Slots: {len(components['slots'])}")
        print(f"- Lambda Functions: {len(components['lambda_functions'])}")
        
        # Display Lambda function details
        if components['lambda_functions']:
            manager.display_lambda_usage_summary(components['lambda_functions'])
        else:
            print("\nNo Lambda functions found with bot export")
            
        # Test without bot export for comparison
        print("\n" + "="*60)
        print("TESTING WITHOUT BOT EXPORT (COMPARISON)")
        print("="*60)
        
        components_no_export = manager.list_bot_components(bot_id, region, export_bot=False)
        
        print(f"\nResults without bot export:")
        print(f"- Intents: {len(components_no_export['intents'])}")
        print(f"- Slots: {len(components_no_export['slots'])}")
        print(f"- Lambda Functions: {len(components_no_export['lambda_functions'])}")
        
        # Compare results
        export_lambda_count = len(components['lambda_functions'])
        no_export_lambda_count = len(components_no_export['lambda_functions'])
        
        print(f"\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)
        print(f"Lambda functions found with bot export: {export_lambda_count}")
        print(f"Lambda functions found without bot export: {no_export_lambda_count}")
        
        if export_lambda_count > no_export_lambda_count:
            print("✅ Bot export found more Lambda functions!")
            print("   This suggests the bot export method is more comprehensive.")
        elif export_lambda_count == no_export_lambda_count:
            print("✅ Both methods found the same number of Lambda functions.")
        else:
            print("⚠️  Bot export found fewer Lambda functions than intent-by-intent analysis.")
            print("   This might indicate an issue with the export analysis.")
            
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
    test_bot_export()