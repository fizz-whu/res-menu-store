#!/usr/bin/env python3
import boto3

# Test specific items you requested
table = boto3.resource('dynamodb', region_name='us-west-2').Table('RestaurantMenuOptimized')

test_items = [
    'Ginger Soy Chicken',
    'Eggplant with Chicken, Shrimp in Special Sauce',
    'Barbecued Pork Wonton Soup',
    'Beef Wonton Soup',
    'Chicken Wonton Soup',
    'Roasted Duck Wonton Soup',
    'Shrimp Wonton Soup',
    'Barbecued Pork Noodle Soup',
    'Beef Noodle Soup',
    'Chicken Noodle Soup',
    'Roasted Duck Noodle Soup',
    'Shrimp Noodle Soup'
]

print('Testing your specifically requested items:')
print('=' * 60)

found_count = 0
for item_name in test_items:
    try:
        response = table.get_item(Key={'sample_name': item_name})
        if 'Item' in response:
            item = response['Item']
            print(f'✅ {item_name}')
            print(f'   Price: ${item["price"]}')
            print(f'   Menu: {item["menu_english_name"]}')
            print(f'   Category: {item["category"]}')
            found_count += 1
        else:
            print(f'❌ {item_name}: Not found')
    except Exception as e:
        print(f'❌ {item_name}: Error - {e}')
    print()

print(f'Summary: {found_count}/{len(test_items)} items found')

# Test order calculation
print('\n' + '=' * 60)
print('Testing order calculation:')

sample_order = [
    {"sample_name": "Kung Pao Chicken", "quantity": 2},
    {"sample_name": "Beef with Broccoli", "quantity": 1},
    {"sample_name": "Barbecued Pork Wonton Soup", "quantity": 1},
    {"sample_name": "Steamed Rice", "quantity": 2}
]

total = 0
print('Order items:')
for order_item in sample_order:
    sample_name = order_item['sample_name']
    quantity = order_item['quantity']
    
    response = table.get_item(Key={'sample_name': sample_name})
    if 'Item' in response:
        price = float(response['Item']['price'])
        line_total = price * quantity
        total += line_total
        print(f'  {quantity}x {sample_name} @ ${price:.2f} = ${line_total:.2f}')
    else:
        print(f'  {quantity}x {sample_name} - NOT FOUND')

tax = total * 0.085
grand_total = total + tax

print(f'\nSubtotal: ${total:.2f}')
print(f'Tax (8.5%): ${tax:.2f}')
print(f'Total: ${grand_total:.2f}')