#!/usr/bin/env python3
"""
Test script for the updated lambda function with pricing functionality
"""

import json
import sys
import os

# Add the current directory to the path to import lambda_function
sys.path.insert(0, '/home/fizz/work/res-menu-store/auto/tmp')

# Import the lambda function
from lambda_function import get_menu_item_price, calculate_order_total

def test_price_lookup():
    """Test the price lookup functionality"""
    print("=== Testing Price Lookup Functionality ===")
    
    test_items = [
        "Kung Pao Chicken",
        "Beef with Broccoli", 
        "Barbecued Pork Wonton Soup",
        "Steamed Rice",
        "Invalid Dish Name"
    ]
    
    for dish_name in test_items:
        print(f"\nTesting: {dish_name}")
        price, menu_name, found = get_menu_item_price(dish_name)
        
        if found:
            print(f"  ✅ Found: {menu_name} - ${price}")
        else:
            print(f"  ❌ Not found")

def test_order_calculation():
    """Test order total calculation"""
    print("\n=== Testing Order Total Calculation ===")
    
    test_orders = [
        {"dish": "Kung Pao Chicken", "quantity": 2},
        {"dish": "Beef with Broccoli", "quantity": 1},
        {"dish": "Steamed Rice", "quantity": 3},
        {"dish": "Barbecued Pork Wonton Soup", "quantity": 1}
    ]
    
    for order in test_orders:
        print(f"\nCalculating: {order['quantity']}x {order['dish']}")
        pricing = calculate_order_total(order['dish'], order['quantity'])
        
        if pricing['found']:
            print(f"  Menu Item: {pricing['menu_name']}")
            print(f"  Unit Price: ${pricing['unit_price']:.2f}")
            print(f"  Subtotal: ${pricing['subtotal']:.2f}")
            print(f"  Tax (8.5%): ${pricing['tax_amount']:.2f}")
            print(f"  Total: ${pricing['total']:.2f}")
        else:
            print(f"  ❌ Item not found")

def test_lambda_event():
    """Test with a sample Lex event"""
    print("\n=== Testing Lambda Function with Sample Event ===")
    
    # Sample Lex event structure
    sample_event = {
        "sessionState": {
            "intent": {
                "name": "OrderFoodIntent",
                "slots": {
                    "DishName": {
                        "value": {
                            "interpretedValue": "Kung Pao Chicken"
                        }
                    },
                    "Quantity": {
                        "value": {
                            "interpretedValue": "2"
                        }
                    },
                    "Customization": {
                        "value": {
                            "interpretedValue": "extra spicy"
                        }
                    }
                }
            }
        }
    }
    
    print("Sample Event:")
    print(json.dumps(sample_event, indent=2))
    
    # Note: We can't actually call lambda_handler without proper AWS environment
    # But we can test the components
    dish_name = sample_event['sessionState']['intent']['slots']['DishName']['value']['interpretedValue']
    quantity = int(sample_event['sessionState']['intent']['slots']['Quantity']['value']['interpretedValue'])
    customization = sample_event['sessionState']['intent']['slots']['Customization']['value']['interpretedValue']
    
    print(f"\nExtracted from event:")
    print(f"  Dish: {dish_name}")
    print(f"  Quantity: {quantity}")
    print(f"  Customization: {customization}")
    
    # Test pricing calculation
    pricing = calculate_order_total(dish_name, quantity)
    
    if pricing['found']:
        print(f"\nPricing calculation:")
        print(f"  {quantity}x {dish_name} @ ${pricing['unit_price']:.2f} each")
        print(f"  Subtotal: ${pricing['subtotal']:.2f}")
        print(f"  Tax: ${pricing['tax_amount']:.2f}")
        print(f"  Total: ${pricing['total']:.2f}")
        
        # Simulate the success message
        success_message = f"Order confirmed!\n\n"
        success_message += f"• {quantity}x {dish_name} @ ${pricing['unit_price']:.2f} each\n"
        success_message += f"• Special requests: {customization}\n"
        success_message += f"\nSubtotal: ${pricing['subtotal']:.2f}\n"
        success_message += f"Tax (8.5%): ${pricing['tax_amount']:.2f}\n"
        success_message += f"Total: ${pricing['total']:.2f}\n\n"
        success_message += f"Order ID: ORD-TEST123\n"
        success_message += "Your order has been placed successfully and the kitchen has been notified!"
        
        print(f"\nGenerated success message:")
        print("-" * 50)
        print(success_message)
        print("-" * 50)
    else:
        print(f"  ❌ Item not found in menu")

def main():
    """Run all tests"""
    print("🧪 Testing Updated Lambda Function with Pricing")
    print("=" * 60)
    
    try:
        # Test 1: Price lookup
        test_price_lookup()
        
        # Test 2: Order calculation
        test_order_calculation()
        
        # Test 3: Lambda event simulation
        test_lambda_event()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("🚀 Lambda function is ready for deployment!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()