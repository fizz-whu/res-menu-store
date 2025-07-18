#!/usr/bin/env python3
"""
Debug script to test Lambda function detection logic
"""

def test_lambda_detection():
    """Test the Lambda function detection without AWS calls"""
    
    # Mock data structures
    mock_components = {
        'intents': [
            {'name': 'WelcomeIntent', 'id': 'intent1'},
            {'name': 'OrderIntent', 'id': 'intent2'}
        ],
        'slots': [
            {'name': 'ProductType', 'id': 'slot1'}
        ],
        'lambda_functions': []  # This should be populated
    }
    
    # Test the display logic
    all_items = []
    
    # Flatten all components into a single list
    for component_type, items in mock_components.items():
        for item in items:
            item['type'] = component_type
            all_items.append(item)
    
    print("Mock components test:")
    print(f"Total items: {len(all_items)}")
    
    for i, item in enumerate(all_items, 1):
        component_type = item['type']
        name = item['name']
        print(f"{i}. [{component_type.upper()}] {name}")
    
    # Now test with Lambda functions
    mock_components['lambda_functions'] = [
        {'name': 'OrderProcessor', 'arn': 'arn:aws:lambda:us-east-1:123456789012:function:OrderProcessor'}
    ]
    
    all_items = []
    for component_type, items in mock_components.items():
        for item in items:
            item['type'] = component_type
            all_items.append(item)
    
    print("\nWith Lambda functions:")
    print(f"Total items: {len(all_items)}")
    
    for i, item in enumerate(all_items, 1):
        component_type = item['type']
        name = item['name']
        print(f"{i}. [{component_type.upper()}] {name}")

if __name__ == "__main__":
    test_lambda_detection()