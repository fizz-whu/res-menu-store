#!/usr/bin/env python3
"""
Example usage of the Lex Bot Manager for Lambda function management
"""

from lex_bot_manager import LexBotManager

def example_lambda_workflow():
    """Example workflow for managing Lambda functions"""
    
    # Initialize the manager
    manager = LexBotManager()
    
    # Read bots from CSV
    bots = manager.read_bot_ids_from_csv()
    
    if not bots:
        print("No bots found in bot_ids.csv")
        return
    
    # Get the first bot for demonstration
    bot = bots[0]
    bot_id = bot['bot_id']
    region = bot['region']
    
    print(f"Analyzing bot: {bot_id} in region: {region}")
    
    # List all components including Lambda functions
    components = manager.list_bot_components(bot_id, region)
    
    print(f"\nFound components:")
    print(f"- Intents: {len(components['intents'])}")
    print(f"- Slots: {len(components['slots'])}")
    print(f"- Lambda Functions: {len(components['lambda_functions'])}")
    
    # Display Lambda function details
    if components['lambda_functions']:
        print(f"\nLambda Functions:")
        for func in components['lambda_functions']:
            print(f"- {func['name']} ({func['runtime']})")
            print(f"  ARN: {func['arn']}")
            print(f"  Handler: {func['handler']}")
            print(f"  Description: {func['description']}")
            print()
    
    # Example of downloading a Lambda function
    if components['lambda_functions']:
        func = components['lambda_functions'][0]
        func['type'] = 'lambda_functions'  # Add type for download
        
        print(f"Downloading Lambda function: {func['name']}")
        file_path = manager.download_component(func)
        
        if file_path:
            print(f"Downloaded to: {file_path}")
            print(f"Source code directory: {file_path.replace('.json', '_code/')}")
            print("\nYou can now:")
            print("1. Edit the JSON file to change function configuration")
            print("2. Edit files in the _code/ directory to modify the source code")
            print("3. Use --upload to push changes back to AWS")

if __name__ == "__main__":
    example_lambda_workflow()