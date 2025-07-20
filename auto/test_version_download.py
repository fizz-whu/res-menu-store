#!/usr/bin/env python3
"""
Test script to download Lambda function code with version information
"""

from lambda_function_manager import LambdaFunctionManager

def test_version_download():
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
    print(f"\n=== Function Details ===")
    print(f"Name: {test_function['name']}")
    print(f"Current Version: {test_function.get('version', '$LATEST')}")
    print(f"Code SHA256: {test_function.get('code_sha256', 'N/A')}")
    print(f"Last Modified: {test_function.get('last_modified', 'N/A')}")
    
    # Show available versions
    versions = test_function.get('versions_available', [])
    if versions:
        print(f"\nAvailable versions ({len(versions)} total):")
        for i, v in enumerate(versions):
            print(f"  {i+1}. Version {v['version']}: {v['last_modified']} (SHA: {v['code_sha256'][:16]}...)")
    
    # Download $LATEST version
    print(f"\n=== Downloading $LATEST version ===")
    result = manager.download_lambda_function(test_function)
    
    if result:
        print(f"Success! Code downloaded to: {result}")
    else:
        print("Download failed")

if __name__ == "__main__":
    test_version_download()