import boto3
import json
import datetime
from decimal import Decimal

# DynamoDB table names
ORDERS_TABLE = "cnres0_orders"
MENU_TABLE = "RestaurantMenuOptimized"

# SNS endpoint ARN
endpoint_arn = "arn:aws:sns:us-west-2:495599767527:endpoint/APNS_SANDBOX/CnResOrderDisplayNotificationDev/e9792aab-7449-3d7b-98ac-2ebf2ef919fc"

# Constants
TAX_RATE = Decimal('0.085')  # 8.5% tax rate

# Family dinner menu mapping
FAMILY_DINNER_MENUS = {
    "Hong Kong": {
        "4": {
            "sample_name": "Hong Kong Family Dinner for 4",
            "dishes": ["Sweet and Sour Pork", "Beef with Broccoli", "Fried Rice", "Wonton Soup"],
            "base_price": Decimal('89.99')
        },
        "6": {
            "sample_name": "Hong Kong Family Dinner for 6", 
            "dishes": ["Sweet and Sour Pork", "Beef with Broccoli", "Kung Pao Chicken", "Fried Rice", "Chow Mein", "Wonton Soup"],
            "base_price": Decimal('129.99')
        },
        "8": {
            "sample_name": "Hong Kong Family Dinner for 8",
            "dishes": ["Sweet and Sour Pork", "Beef with Broccoli", "Kung Pao Chicken", "Orange Chicken", "Fried Rice", "Chow Mein", "Wonton Soup", "Hot and Sour Soup"],
            "base_price": Decimal('169.99')
        }
    },
    "Peking": {
        "4": {
            "sample_name": "Peking Family Dinner for 4",
            "dishes": ["Peking Duck", "Mapo Tofu", "Fried Rice", "Hot and Sour Soup"],
            "base_price": Decimal('99.99')
        },
        "6": {
            "sample_name": "Peking Family Dinner for 6",
            "dishes": ["Peking Duck", "Mapo Tofu", "Kung Pao Chicken", "Fried Rice", "Lo Mein", "Hot and Sour Soup"],
            "base_price": Decimal('149.99')
        },
        "8": {
            "sample_name": "Peking Family Dinner for 8", 
            "dishes": ["Peking Duck", "Mapo Tofu", "Kung Pao Chicken", "General Tso's Chicken", "Fried Rice", "Lo Mein", "Hot and Sour Soup", "Wonton Soup"],
            "base_price": Decimal('199.99')
        }
    }
}

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
sns_client = boto3.client('sns', region_name='us-west-2')

def get_menu_item_price(dish_name):
    """
    Get price for a menu item from the RestaurantMenuOptimized table
    
    Args:
        dish_name: Sample name of the dish (e.g., "Kung Pao Chicken")
        
    Returns:
        tuple: (price_decimal, menu_english_name, found) or (None, None, False) if not found
    """
    try:
        menu_table = dynamodb.Table(MENU_TABLE)
        
        # Try direct lookup by sample name (primary key)
        response = menu_table.get_item(Key={'sample_name': dish_name})
        
        if 'Item' in response:
            item = response['Item']
            price = item['price']
            menu_name = item['menu_english_name']
            return Decimal(str(price)), menu_name, True
        else:
            print(f"Menu item not found: {dish_name}")
            return None, None, False
            
    except Exception as e:
        print(f"Error getting menu item price for {dish_name}: {str(e)}")
        return None, None, False

def calculate_order_total(dish_name, quantity):
    """
    Calculate total price for an order including tax
    
    Args:
        dish_name: Name of the dish
        quantity: Quantity ordered
        
    Returns:
        dict: {
            'unit_price': Decimal,
            'subtotal': Decimal, 
            'tax_amount': Decimal,
            'total': Decimal,
            'menu_name': str,
            'found': bool
        }
    """
    unit_price, menu_name, found = get_menu_item_price(dish_name)
    
    if not found:
        return {
            'unit_price': Decimal('0'),
            'subtotal': Decimal('0'),
            'tax_amount': Decimal('0'),
            'total': Decimal('0'),
            'menu_name': dish_name,
            'found': False
        }
    
    subtotal = unit_price * Decimal(str(quantity))
    tax_amount = subtotal * TAX_RATE
    total = subtotal + tax_amount
    
    return {
        'unit_price': unit_price,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total': total,
        'menu_name': menu_name,
        'found': True
    }

def get_family_dinner_details(style, number_of_people):
    """
    Get family dinner details based on style and number of people
    
    Args:
        style: Family dinner style (Hong Kong or Peking)
        number_of_people: Number of people (as string)
        
    Returns:
        tuple: (menu_details, found) or (None, False) if not found
    """
    try:
        # Normalize style input
        style_normalized = style.title() if style else "Hong Kong"
        if style_normalized not in FAMILY_DINNER_MENUS:
            style_normalized = "Hong Kong"  # Default fallback
            
        # Handle number of people - round up to next available size
        people_count = str(number_of_people)
        if people_count not in FAMILY_DINNER_MENUS[style_normalized]:
            # Find the next larger size available
            available_sizes = sorted([int(size) for size in FAMILY_DINNER_MENUS[style_normalized].keys()])
            target_size = None
            for size in available_sizes:
                if size >= int(number_of_people):
                    target_size = str(size)
                    break
            
            if target_size is None:
                # Use largest available size
                target_size = str(max(available_sizes))
                
            people_count = target_size
            
        menu_details = FAMILY_DINNER_MENUS[style_normalized][people_count].copy()
        menu_details['actual_style'] = style_normalized
        menu_details['actual_size'] = people_count
        return menu_details, True
        
    except Exception as e:
        print(f"Error getting family dinner details: {str(e)}")
        return None, False

def calculate_family_dinner_total(style, number_of_people):
    """
    Calculate total price for a family dinner including tax
    
    Args:
        style: Family dinner style
        number_of_people: Number of people
        
    Returns:
        dict: Pricing details and menu information
    """
    menu_details, found = get_family_dinner_details(style, number_of_people)
    
    if not found:
        return {
            'base_price': Decimal('0'),
            'tax_amount': Decimal('0'),
            'total': Decimal('0'),
            'menu_name': f"{style} Family Dinner for {number_of_people}",
            'dishes': [],
            'found': False
        }
    
    base_price = menu_details['base_price']
    tax_amount = base_price * TAX_RATE
    total = base_price + tax_amount
    
    return {
        'base_price': base_price,
        'tax_amount': tax_amount,
        'total': total,
        'menu_name': menu_details['sample_name'],
        'dishes': menu_details['dishes'],
        'actual_style': menu_details['actual_style'],
        'actual_size': menu_details['actual_size'],
        'found': True
    }

def handle_order_food_intent(event, intent_name, slots):
    """
    Handle OrderFood intent for individual dish orders
    """
    # Fixed slot names to match actual Lex event
    dish_name = slots['DishName']['value']['interpretedValue']
    quantity = int(slots['Quantity']['value']['interpretedValue'])
    
    # Handle optional Customization slot
    customization = None
    if slots.get('Customization') and slots['Customization']:
        if isinstance(slots['Customization']['value'], dict):
            # Single value
            customization = slots['Customization']['value']['interpretedValue']
        elif isinstance(slots['Customization']['value'], list):
            # Multiple values
            customization = [item['interpretedValue'] for item in slots['Customization']['value']]
    
    print(f"Intent: {intent_name}, DishName: {dish_name}, Quantity: {quantity}, Customization: {customization}")
    
    # Calculate order total and pricing
    pricing = calculate_order_total(dish_name, quantity)
    
    if not pricing['found']:
        # Item not found in menu
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': intent_name,
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': f"Sorry, '{dish_name}' is not available on our menu. Please try a different dish."
                }
            ]
        }
    
    # Store order in DynamoDB with pricing information
    orders_table = dynamodb.Table(ORDERS_TABLE)
    order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.datetime.now().isoformat()
    
    # Prepare order item with pricing
    order_item = {
        'OrderID': order_id,
        'Timestamp': timestamp,
        'DishName': dish_name,
        'MenuName': pricing['menu_name'],
        'Quantity': quantity,
        'UnitPrice': pricing['unit_price'],
        'Subtotal': pricing['subtotal'],
        'TaxAmount': pricing['tax_amount'],
        'Total': pricing['total'],
        'Status': 'Pending',
        'OrderType': 'IndividualDish'
    }
    
    # Add customization if present
    if customization:
        order_item['Customization'] = customization
    
    orders_table.put_item(Item=order_item)
    
    print(f"Order saved with total: ${pricing['total']:.2f}")
    
    # Build notification message with pricing
    customization_text = ""
    if customization:
        if isinstance(customization, list):
            customization_text = f", 特殊要求: {', '.join(customization)}"
        else:
            customization_text = f", 特殊要求: {customization}"
    
    notification_message = f"菜品名称: {dish_name}, 数量: {quantity}, 单价: ${pricing['unit_price']:.2f}, 总计: ${pricing['total']:.2f}{customization_text}, 状态: 待处理"
    
    # Send notification
    payload = {
        "default": "New order notification",
        "APNS_SANDBOX": json.dumps({
            "aps": {
                "alert": {
                    "title": "New Order",
                    "body": notification_message
                },
                "sound": "default",
                "badge": 1
            }
        })
    }
    
    sns_client.publish(
        TargetArn=endpoint_arn,
        MessageStructure='json',
        Message=json.dumps(payload)
    )
    
    # Build success response message with pricing
    success_message = f"Order confirmed!\n\n"
    success_message += f"• {quantity}x {dish_name} @ ${pricing['unit_price']:.2f} each\n"
    if customization:
        if isinstance(customization, list):
            success_message += f"• Special requests: {', '.join(customization)}\n"
        else:
            success_message += f"• Special requests: {customization}\n"
    success_message += f"\nSubtotal: ${pricing['subtotal']:.2f}\n"
    success_message += f"Tax (8.5%): ${pricing['tax_amount']:.2f}\n"
    success_message += f"Total: ${pricing['total']:.2f}\n\n"
    success_message += f"Order ID: {order_id}\n"
    success_message += "Your order has been placed successfully and the kitchen has been notified!"
    
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': intent_name,
                'state': 'Fulfilled'
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': success_message
            }
        ]
    }

def handle_order_family_dinner_intent(event, intent_name, slots):
    """
    Handle OrderFamilyDinnerIntent for family dinner packages
    """
    # Extract slot values for family dinner
    number_of_people = 4  # Default value
    if slots.get('NumberOfPeople') and slots['NumberOfPeople']:
        number_of_people = int(slots['NumberOfPeople']['value']['interpretedValue'])
    
    family_dinner_style = "Hong Kong"  # Default value
    if slots.get('FamilyDinnerStyle') and slots['FamilyDinnerStyle']:
        family_dinner_style = slots['FamilyDinnerStyle']['value']['interpretedValue']
    
    print(f"Intent: {intent_name}, NumberOfPeople: {number_of_people}, FamilyDinnerStyle: {family_dinner_style}")
    
    # Calculate family dinner pricing
    pricing = calculate_family_dinner_total(family_dinner_style, number_of_people)
    
    if not pricing['found']:
        # Family dinner not available
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': intent_name,
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': f"Sorry, the {family_dinner_style} family dinner for {number_of_people} people is not available. Please try a different option."
                }
            ]
        }
    
    # Store order in DynamoDB
    orders_table = dynamodb.Table(ORDERS_TABLE)
    order_id = f"FAM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.datetime.now().isoformat()
    
    # Prepare family dinner order item
    order_item = {
        'OrderID': order_id,
        'Timestamp': timestamp,
        'DishName': pricing['menu_name'],
        'MenuName': pricing['menu_name'],
        'FamilyDinnerStyle': pricing['actual_style'],
        'NumberOfPeople': int(pricing['actual_size']),
        'RequestedPeople': number_of_people,
        'Dishes': pricing['dishes'],
        'Quantity': 1,
        'BasePrice': pricing['base_price'],
        'TaxAmount': pricing['tax_amount'],
        'Total': pricing['total'],
        'Status': 'Pending',
        'OrderType': 'FamilyDinner'
    }
    
    orders_table.put_item(Item=order_item)
    
    print(f"Family dinner order saved with total: ${pricing['total']:.2f}")
    
    # Build notification message
    dishes_text = ", ".join(pricing['dishes'])
    notification_message = f"家庭套餐订单: {pricing['actual_style']} 风味, {pricing['actual_size']}人份, 包含: {dishes_text}, 总计: ${pricing['total']:.2f}, 状态: 待处理"
    
    # Send notification
    payload = {
        "default": "New family dinner order notification",
        "APNS_SANDBOX": json.dumps({
            "aps": {
                "alert": {
                    "title": "New Family Dinner Order",
                    "body": notification_message
                },
                "sound": "default",
                "badge": 1
            }
        })
    }
    
    sns_client.publish(
        TargetArn=endpoint_arn,
        MessageStructure='json',
        Message=json.dumps(payload)
    )
    
    # Build success response message
    success_message = f"Family Dinner Order Confirmed!\n\n"
    success_message += f"• {pricing['actual_style']} Style Family Dinner\n"
    success_message += f"• Serves {pricing['actual_size']} people"
    if int(pricing['actual_size']) != number_of_people:
        success_message += f" (upgraded from {number_of_people} people)"
    success_message += f"\n\nIncluded dishes:\n"
    for dish in pricing['dishes']:
        success_message += f"  - {dish}\n"
    success_message += f"\nBase Price: ${pricing['base_price']:.2f}\n"
    success_message += f"Tax (8.5%): ${pricing['tax_amount']:.2f}\n"
    success_message += f"Total: ${pricing['total']:.2f}\n\n"
    success_message += f"Order ID: {order_id}\n"
    success_message += "Your family dinner order has been placed successfully and the kitchen has been notified!"
    
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': intent_name,
                'state': 'Fulfilled'
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': success_message
            }
        ]
    }

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    
    try:
        # Extract intent and slots
        intent_name = event['sessionState']['intent']['name']
        slots = event['sessionState']['intent']['slots']
        
        print(f"Processing intent: {intent_name}")
        
        # Route to appropriate handler based on intent name
        if intent_name == 'OrderFamilyDinnerIntent':
            return handle_order_family_dinner_intent(event, intent_name, slots)
        elif intent_name in ['OrderFood', 'OrderFoodIntent']:
            return handle_order_food_intent(event, intent_name, slots)
        else:
            # Unknown intent
            return {
                'sessionState': {
                    'dialogAction': {
                        'type': 'Close'
                    },
                    'intent': {
                        'name': intent_name,
                        'state': 'Failed'
                    }
                },
                'messages': [
                    {
                        'contentType': 'PlainText',
                        'content': f"Sorry, I don't know how to handle the intent '{intent_name}'. Please try again."
                    }
                ]
            }
    
    except KeyError as e:
        print(f"KeyError - Missing slot: {e}")
        print("Available slots:", list(slots.keys()) if 'slots' in locals() else "No slots found")
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'] if 'sessionState' in event else 'Unknown',
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': f"Missing required information: {str(e)}. Please try again."
                }
            ]
        }
    
    except Exception as e:
        print("Error:", e)
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'] if 'sessionState' in event else 'Unknown',
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': "An error occurred while processing your request. Please try again."
                }
            ]
        }