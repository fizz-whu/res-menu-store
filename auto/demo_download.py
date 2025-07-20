#!/usr/bin/env python3
"""
Demo: Download test_dynamo_write_0 Lambda function source code
"""

from lambda_function_manager import LambdaFunctionManager

def demo_download_specific_function():
    manager = LambdaFunctionManager(debug=True)
    
    # Step 1: Get all functions in the region
    region = 'us-west-2'
    print(f"Step 1: Fetching Lambda functions in region: {region}")
    functions = manager.list_lambda_functions(region)
    
    # Step 2: Find the specific function we want
    target_function = None
    for func in functions:
        if func['name'] == 'test_dynamo_write_0':
            target_function = func
            break
    
    if not target_function:
        print("❌ Function 'test_dynamo_write_0' not found!")
        print("Available functions:")
        for func in functions:
            print(f"  - {func['name']}")
        return
    
    # Step 3: Show function details
    print(f"\n📋 Step 2: Found target function details:")
    print(f"   Name: {target_function['name']}")
    print(f"   Runtime: {target_function['runtime']}")
    print(f"   Handler: {target_function['handler']}")
    print(f"   Version: {target_function.get('version', '$LATEST')}")
    print(f"   Code SHA256: {target_function.get('code_sha256', 'N/A')}")
    print(f"   Last Modified: {target_function.get('last_modified', 'N/A')}")
    print(f"   Code Size: {target_function.get('code_size', 'N/A')} bytes")
    
    # Step 4: Download the source code
    print(f"\n🔽 Step 3: Downloading source code...")
    result = manager.download_lambda_function(target_function)
    
    if result:
        print(f"\n✅ Step 4: Download successful!")
        print(f"   Code downloaded to: {result}")
        
        # Step 5: Show what was downloaded
        import os
        files = os.listdir(result)
        print(f"   Files extracted: {files}")
        
        # Step 6: Show the actual source code
        print(f"\n📄 Step 5: Source code preview:")
        print("-" * 50)
        
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.go', '.cs', '.rb')):
                file_path = os.path.join(result, file)
                print(f"\n--- {file} ---")
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # Show first 30 lines
                        lines = content.split('\n')
                        for i, line in enumerate(lines[:30], 1):
                            print(f"{i:2d}: {line}")
                        if len(lines) > 30:
                            print(f"... ({len(lines) - 30} more lines)")
                except Exception as e:
                    print(f"Error reading {file}: {e}")
        
        print("-" * 50)
        print(f"✅ Demo complete! Source code is available in: {result}")
        
    else:
        print("❌ Download failed!")

if __name__ == "__main__":
    demo_download_specific_function()