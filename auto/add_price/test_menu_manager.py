#!/usr/bin/env python3
"""
Test script for menu DynamoDB manager without requiring AWS credentials
"""

import json
import sys
import os

def test_sample_extraction():
    """Test extracting sample values from DishType.json"""
    print("=== Testing Sample Value Extraction ===")
    
    json_file = '/home/fizz/work/res-menu-store/auto/tmp/DishType.json'
    
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        sample_values = []
        sample_data = {}
        
        for slot_type_value in data.get('slotTypeValues', []):
            sample_value = slot_type_value.get('sampleValue', {}).get('value')
            if sample_value:
                sample_values.append(sample_value)
                
                # Extract synonyms
                synonyms = []
                chinese_synonym = ""
                for synonym in slot_type_value.get('synonyms', []):
                    synonym_value = synonym.get('value', '')
                    if synonym_value:
                        synonyms.append(synonym_value)
                        # Check for Chinese characters
                        if any('\u4e00' <= char <= '\u9fff' for char in synonym_value):
                            chinese_synonym = synonym_value
                
                sample_data[sample_value] = {
                    'synonyms': synonyms,
                    'chinese_synonym': chinese_synonym
                }
        
        print(f"✅ Found {len(sample_values)} sample values")
        
        # Show first few samples
        print("\nFirst 10 sample values:")
        for i, sample in enumerate(sample_values[:10]):
            synonyms = sample_data[sample]['synonyms']
            chinese = sample_data[sample]['chinese_synonym']
            print(f"  {i+1}. {sample}")
            print(f"     Chinese: {chinese}")
            print(f"     Synonyms: {len(synonyms)} items")
        
        return sample_values, sample_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return [], {}


def test_price_mapping():
    """Test creating price mappings"""
    print("\n=== Testing Price Mapping ===")
    
    # Hard-coded menu prices (subset for testing)
    MENU_PRICES = {
        "KUNG PAO CHICKEN": "13.25",
        "BEEF W/ BROCCOLI": "14.25",
        "SWEET & SOUR CHICKEN": "13.25",
        "STEAMED RICE": "1.75",
        "BARBECUED PORK WONTON SOUP": "10.50",
        "BEEF WONTON SOUP": "10.50",
        "CHICKEN WONTON SOUP": "10.50",
        "EGGPLANT W/ CHICKEN, SHRIMP IN SPECIAL SAUCE": "14.75"
    }
    
    # Sample mappings
    SAMPLE_MAPPINGS = {
        "Kung Pao Chicken": "KUNG PAO CHICKEN",
        "Beef with Broccoli": "BEEF W/ BROCCOLI", 
        "Sweet & Sour Chicken": "SWEET & SOUR CHICKEN",
        "Steamed Rice": "STEAMED RICE",
        "Barbecued Pork Wonton Soup": "BARBECUED PORK WONTON SOUP",
        "Beef Wonton Soup": "BEEF WONTON SOUP",
        "Chicken Wonton Soup": "CHICKEN WONTON SOUP",
        "Eggplant with Chicken, Shrimp in Special Sauce": "EGGPLANT W/ CHICKEN, SHRIMP IN SPECIAL SAUCE"
    }
    
    # Get sample values
    sample_values, _ = test_sample_extraction()
    
    print(f"\nCreating mappings for {len(sample_values)} sample values...")
    
    mapping = {}
    mapped_count = 0
    
    for sample_value in sample_values:
        # Try exact mapping first
        if sample_value in SAMPLE_MAPPINGS:
            menu_name = SAMPLE_MAPPINGS[sample_value]
            if menu_name in MENU_PRICES:
                price = MENU_PRICES[menu_name]
                mapping[sample_value] = {
                    'menu_name': menu_name,
                    'price': price,
                    'mapped': True
                }
                mapped_count += 1
                continue
        
        # Default mapping
        mapping[sample_value] = {
            'menu_name': sample_value,
            'price': '12.00',
            'mapped': False
        }
    
    print(f"✅ Created mappings for {len(mapping)} items")
    print(f"✅ Successfully mapped {mapped_count} items to menu prices")
    print(f"⚠️  {len(mapping) - mapped_count} items using default price")
    
    # Show successfully mapped items
    print("\nSuccessfully mapped items:")
    for sample_name, data in mapping.items():
        if data['mapped']:
            print(f"  • {sample_name} -> {data['menu_name']} (${data['price']})")
    
    return mapping


def test_order_calculation():
    """Test order total calculation"""
    print("\n=== Testing Order Calculation ===")
    
    # Sample order
    sample_order = [
        {"sample_name": "Kung Pao Chicken", "quantity": 2},
        {"sample_name": "Beef with Broccoli", "quantity": 1},
        {"sample_name": "Steamed Rice", "quantity": 2}
    ]
    
    # Get mapping
    mapping = test_price_mapping()
    
    print(f"\nCalculating total for sample order:")
    order_details = []
    subtotal = 0.0
    items_not_found = []
    
    for order_item in sample_order:
        sample_name = order_item.get('sample_name', '')
        quantity = int(order_item.get('quantity', 1))
        
        print(f"  {quantity}x {sample_name}")
        
        if sample_name in mapping:
            unit_price = float(mapping[sample_name]['price'])
            line_total = unit_price * quantity
            
            order_details.append({
                'sample_name': sample_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total
            })
            
            subtotal += line_total
            print(f"    @ ${unit_price} each = ${line_total:.2f}")
        else:
            items_not_found.append(sample_name)
            print(f"    ❌ Not found in menu")
    
    # Calculate tax
    tax_rate = 0.085
    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount
    
    print(f"\nOrder Summary:")
    print(f"  Subtotal: ${subtotal:.2f}")
    print(f"  Tax (8.5%): ${tax_amount:.2f}")
    print(f"  Total: ${total:.2f}")
    
    if items_not_found:
        print(f"  Items not found: {items_not_found}")
    
    return {
        'order_details': order_details,
        'items_not_found': items_not_found,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total': total
    }


def test_dynamo_structure():
    """Test the DynamoDB table structure (without actual AWS calls)"""
    print("\n=== Testing DynamoDB Table Structure ===")
    
    # Get sample data
    sample_values, sample_data = test_sample_extraction()
    mapping = test_price_mapping()
    
    print("Preparing DynamoDB items...")
    
    items = []
    for sample_name, sample_info in list(sample_data.items())[:5]:  # Test first 5
        menu_mapping = mapping.get(sample_name, {})
        
        item = {
            'sample_name': sample_name,  # Primary key
            'menu_english_name': menu_mapping.get('menu_name', sample_name),
            'menu_chinese_name': sample_info.get('chinese_synonym', ''),
            'category': 'TEST_CATEGORY',
            'price': float(menu_mapping.get('price', '12.00')),
            'price_display': f"${menu_mapping.get('price', '12.00')}",
            'available': True,
            'synonyms': sample_info.get('synonyms', []),
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
        
        items.append(item)
    
    print(f"✅ Prepared {len(items)} DynamoDB items")
    
    # Show structure of first item
    print("\nSample DynamoDB item structure:")
    if items:
        sample_item = items[0]
        for key, value in sample_item.items():
            if isinstance(value, list) and len(value) > 3:
                print(f"  {key}: [{len(value)} items] {value[:2]}...")
            else:
                print(f"  {key}: {value}")
    
    return items


def main():
    """Run all tests"""
    print("🚀 Testing Menu DynamoDB Manager Components")
    print("=" * 60)
    
    try:
        # Test 1: Sample value extraction
        sample_values, sample_data = test_sample_extraction()
        
        # Test 2: Price mapping
        mapping = test_price_mapping()
        
        # Test 3: Order calculation
        order_result = test_order_calculation()
        
        # Test 4: DynamoDB structure
        dynamo_items = test_dynamo_structure()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Sample values: {len(sample_values)}")
        print(f"   • Price mappings: {len(mapping)}")
        print(f"   • Test order total: ${order_result['total']:.2f}")
        print(f"   • DynamoDB items prepared: {len(dynamo_items)}")
        
        print(f"\n✅ Ready to create DynamoDB table with {len(sample_values)} menu items!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()