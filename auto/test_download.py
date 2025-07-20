#!/usr/bin/env python3
"""
Test script to download a specific Lambda function code
"""

from lambda_function_manager import LambdaFunctionManager

def test_download():
    manager = LambdaFunctionManager(debug=True)
    
    # Get functions from us-west-2
    region = 'us-west-2'
    print(f"Fetching Lambda functions in region: {region}")
    
    functions = manager.list_lambda_functions(region)
    
    if not functions:
        print("No functions found")
        return
    
    # Pick the first function for testing
    test_function = functions[0]
    print(f"\nDownloading function: {test_function['name']}")
    
    # Download the function code
    result = manager.download_lambda_function(test_function)
    
    if result:
        print(f"Success! Code downloaded to: {result}")
    else:
        print("Download failed")

if __name__ == "__main__":
    test_download()