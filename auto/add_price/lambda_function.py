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

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    
    try:
        # Extract intent and slots
        intent_name = event['sessionState']['intent']['name']
        slots = event['sessionState']['intent']['slots']
        
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
            'UnitPrice': float(pricing['unit_price']),
            'Subtotal': float(pricing['subtotal']),
            'TaxAmount': float(pricing['tax_amount']),
            'Total': float(pricing['total']),
            'Status': 'Pending'
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
                    'content': "An error occurred while placing your order. Please try again."
                }
            ]
        }