#!/usr/bin/env python3
"""
Compare all Lambda functions to help identify the right one
"""

from lambda_function_manager import LambdaFunctionManager

def compare_all_functions():
    manager = LambdaFunctionManager(debug=False)  # Turn off debug for cleaner output
    
    region = 'us-west-2'
    functions = manager.list_lambda_functions(region)
    
    print(f"=== All Lambda Functions in {region} ===")
    print(f"{'Function Name':<25} {'Version':<10} {'Last Modified':<25} {'SHA256':<20} {'Size'}")
    print("-" * 100)
    
    for func in functions:
        name = func['name'][:24]
        version = func.get('version', 'N/A')[:9]
        modified = func.get('last_modified', 'N/A')[:24]
        sha = func.get('code_sha256', 'N/A')[:19]
        size = func.get('code_size', 0)
        
        print(f"{name:<25} {version:<10} {modified:<25} {sha:<20} {size}")
    
    print(f"\n=== Quick download test ===")
    print("Which function would you like to download? (Enter number)")
    for i, func in enumerate(functions, 1):
        print(f"{i}. {func['name']}")
    
    try:
        choice = int(input("Enter choice: "))
        if 1 <= choice <= len(functions):
            selected = functions[choice - 1]
            print(f"\nDownloading {selected['name']}...")
            
            result = manager.download_lambda_function(selected)
            if result:
                print(f"Downloaded to: {result}")
            else:
                print("Download failed")
        else:
            print("Invalid choice")
    except (ValueError, EOFError):
        print("No selection made")

if __name__ == "__main__":
    compare_all_functions()