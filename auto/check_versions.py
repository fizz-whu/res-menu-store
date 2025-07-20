#!/usr/bin/env python3
"""
Script to check all versions of a Lambda function and compare code
"""

import boto3
from lambda_function_manager import LambdaFunctionManager

def check_all_versions():
    manager = LambdaFunctionManager(debug=True)
    
    # Get functions from us-west-2
    region = 'us-west-2'
    function_name = 'cnres0_api_orders_get'  # Change this to your function
    
    lambda_client = boto3.client('lambda', region_name=region)
    
    print(f"=== Checking all versions of {function_name} ===")
    
    try:
        # List all versions
        response = lambda_client.list_versions_by_function(FunctionName=function_name)
        
        for version in response['Versions']:
            print(f"\n--- Version {version['Version']} ---")
            print(f"Last Modified: {version['LastModified']}")
            print(f"Code SHA256: {version['CodeSha256']}")
            print(f"Code Size: {version['CodeSize']} bytes")
            print(f"Description: {version.get('Description', 'No description')}")
            
            # Get the actual function to see the code location
            func_response = lambda_client.get_function(
                FunctionName=function_name,
                Qualifier=version['Version']
            )
            code_location = func_response['Code'].get('Location', 'N/A')
            print(f"Code Location: {code_location[:100]}..." if len(code_location) > 100 else f"Code Location: {code_location}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_versions()