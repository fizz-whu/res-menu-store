#!/usr/bin/env python3
"""
Enhanced Lambda Function with Pricing Integration
Integrates with the pricing system to provide order totals and price inquiries
"""

import boto3
import json
import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import re


class MenuPricingService:
    """Simplified pricing service for Lambda deployment"""
    
    def __init__(self):
        self.menu_prices = self.load_hardcoded_prices()
    
    def load_hardcoded_prices(self) -> Dict:
        """Load menu prices - in production, this would come from DynamoDB"""
        return {
            # House Special
            "spicy salt pepper shrimp": 16.25,
            "minced chicken in lettuce cup": 16.25,
            "walnut prawns": 16.25,
            "rainbow fish fillet": 13.25,
            "orange peel beef": 13.25,
            "orange peel chicken": 13.25,
            "ginger green onion with oyster": 14.25,
            "crispy fried oyster": 14.25,
            "ginger soy chicken": 13.25,
            "crispy fried squid with spicy pepper": 14.25,
            "fried tofu with green bean in dry spicy garlic": 12.75,
            "eggplant with chicken shrimp in special sauce": 14.75,
            "spicy salt pepper pork chop": 13.25,
            "yellow onion pork": 13.25,
            "spicy salt pepper chicken wings": 14.25,
            "generals chicken wings": 14.25,
            
            # Appetizers
            "honey glazed barbecued pork": 10.75,
            "crispy fried prawns": 14.75,
            "golden pot stickers": 9.00,
            "spring egg rolls": 9.00,
            "chicken salad": 8.75,
            
            # Soup
            "hot sour soup": 9.00,
            "minced beef with egg white soup": 9.00,
            "mixed vegetable soup": 9.00,
            "seaweed with egg flower soup": 9.00,
            "seafood bean cake soup": 10.50,
            "wor wonton soup": 11.50,
            "chicken with corn soup": 9.00,
            
            # Fowl/Chicken
            "cashew almond chicken": 13.25,
            "sweet sour chicken": 13.25,
            "lemon chicken": 13.25,
            "chicken with double mushrooms": 13.25,
            "rainbow chicken": 13.25,
            "chicken with black bean sauce": 13.25,
            "curry chicken": 13.25,
            "kung pao chicken": 13.25,
            "chicken with broccoli": 13.25,
            "roasted duck half": 14.00,
            "fried chicken half": 12.00,
            "chicken with mixed vegetables": 13.25,
            
            # Pork
            "cantonese style spareribs": 13.25,
            "spicy hot bean curd with minced pork": 13.25,
            "succulent spicy pork with garlic sauce": 13.25,
            "supremed pork ham sour pork": 13.25,
            "mu shu pork": 13.25,
            "spareribs with black bean sauce": 13.25,
            "barbecued pork with bean cake": 13.25,
            "barbecued pork with mixed vegetables": 13.25,
            
            # Beef
            "peking spicy beef": 14.25,
            "mongolian beef": 14.25,
            "curry beef": 14.25,
            "beef with black bean sauce": 14.25,
            "beef with broccoli": 14.25,
            "beef with oyster sauce": 14.25,
            "beef with snow peas": 14.25,
            "beef with mixed vegetables": 14.25,
            
            # Seafood
            "shrimp chicken with cashew almond": 14.50,
            "shrimp with snow peas": 14.50,
            "shrimp with double mushrooms": 14.50,
            "shrimp with lobster sauce": 14.50,
            "supremed sweet sour shrimp": 14.50,
            "kung pao shrimp": 14.50,
            "curry shrimp": 14.50,
            "shrimp with cashew": 14.50,
            "seafood deluxe": 14.50,
            "clams with ginger scallions": 14.50,
            "clams with black bean sauce": 14.50,
            "braised fish fillet": 14.50,
            "fish fillet in black bean sauce": 14.50,
            "sweet and sour whole fish": 22.00,
            "steamed whole fish": 22.00,
            
            # Vegetables
            "fresh vegetables deluxe": 11.00,
            "snow peas with water chestnuts": 11.00,
            "eggplant with garlic sauce": 11.00,
            "broccoli with oyster sauce": 11.00,
            "vegetarians special": 11.00,
            "double mushroom with oyster sauce": 11.00,
            "braised bean cake": 11.00,
            "mixed vegetables with bean cake": 12.00,
            "house special bean cake": 12.00,
            "kung pao to fu": 12.00,
            
            # Noodles and Rice
            "house special chow mein": 12.25,
            "barbecued pork chow mein": 10.00,
            "chicken chow mein": 10.00,
            "beef with tomato chow mein": 10.00,
            "shrimp chow mein": 10.75,
            "house special fried rice": 12.00,
            "shrimp fried rice": 11.00,
            "yang chow fried rice": 11.00,
            "barbecued pork fried rice": 10.00,
            "chicken fried rice": 10.00,
            "beef fried rice": 10.00,
            "fresh vegetables fried rice": 10.00,
            "steamed rice": 1.75,
            
            # Common variations and simplifications
            "sweet and sour chicken": 13.25,
            "general tso chicken": 14.25,
            "orange chicken": 13.25,
            "broccoli beef": 14.25,
            "mongolian beef": 14.25,
            "cashew chicken": 13.25,
            "kung pao chicken": 13.25,
            "sweet and sour pork": 13.25,
            "egg rolls": 9.00,
            "pot stickers": 9.00,
            "hot and sour soup": 9.00,
            "wonton soup": 11.50,
            "fried rice": 10.00,
            "chow mein": 10.00,
        }
    
    def normalize_dish_name(self, dish_name: str) -> str:
        """Normalize dish name for matching"""
        # Convert to lowercase
        normalized = dish_name.lower().strip()
        
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Replace common variations
        replacements = {
            'w/': 'with',
            '&': 'and',
            'and': '',
            'the': '',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Clean up extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def find_price(self, dish_name: str) -> Optional[float]:
        """Find price for a dish using fuzzy matching"""
        normalized_input = self.normalize_dish_name(dish_name)
        
        # Direct match
        if normalized_input in self.menu_prices:
            return self.menu_prices[normalized_input]
        
        # Partial matching - check if input contains key words from menu items
        for menu_item, price in self.menu_prices.items():
            # Check if all words in the shorter string are in the longer string
            input_words = set(normalized_input.split())
            menu_words = set(menu_item.split())
            
            # If most words match, consider it a match
            if len(input_words.intersection(menu_words)) >= min(len(input_words), len(menu_words)) - 1:
                return price
        
        return None
    
    def calculate_order_total(self, dish_name: str, quantity: int, customizations: List[str] = None) -> Dict:
        """Calculate total for an order"""
        base_price = self.find_price(dish_name)
        
        if base_price is None:
            return {
                'success': False,
                'error': f'Price not found for "{dish_name}"',
                'dish_name': dish_name,
                'quantity': quantity
            }
        
        # Calculate customization charges
        customization_charge = 0.0
        customization_details = []
        
        if customizations:
            for custom in customizations:
                charge = self.get_customization_charge(custom)
                if charge > 0:
                    customization_charge += charge
                    customization_details.append(f"{custom}: +${charge:.2f}")
        
        total_base = base_price * quantity
        total_customization = customization_charge * quantity
        final_total = total_base + total_customization
        
        return {
            'success': True,
            'dish_name': dish_name,
            'quantity': quantity,
            'base_price': base_price,
            'total_base': total_base,
            'customization_charge': customization_charge,
            'customization_details': customization_details,
            'final_total': round(final_total, 2)
        }
    
    def get_customization_charge(self, customization: str) -> float:
        """Get charge for customizations"""
        custom_lower = customization.lower()
        
        # Define charges
        if 'extra sauce' in custom_lower:
            return 0.50
        elif 'extra vegetables' in custom_lower or 'extra veggie' in custom_lower:
            return 1.00
        elif 'extra meat' in custom_lower or 'extra chicken' in custom_lower or 'extra beef' in custom_lower:
            return 2.00
        elif 'extra rice' in custom_lower:
            return 1.75
        else:
            return 0.0  # Most customizations are free


# Global pricing service instance
pricing_service = MenuPricingService()

# DynamoDB and SNS configuration
ORDERS_TABLE = "cnres0_orders"
endpoint_arn = "arn:aws:sns:us-west-2:495599767527:endpoint/APNS_SANDBOX/CnResOrderDisplayNotificationDev/e9792aab-7449-3d7b-98ac-2ebf2ef919fc"

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns', region_name='us-west-2')


def lambda_handler(event, context):
    """Main Lambda handler with pricing integration"""
    print("Event received:", json.dumps(event))
    
    try:
        intent_name = event['sessionState']['intent']['name']
        slots = event['sessionState']['intent']['slots']
        
        if intent_name == 'OrderFood':
            return handle_order_food(event, slots)
        elif intent_name == 'GetPrice':
            return handle_get_price(event, slots)
        elif intent_name == 'CheckMenu':
            return handle_check_menu(event, slots)
        else:
            return handle_unknown_intent(event, intent_name)
            
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return create_error_response(event, str(e))


def handle_order_food(event, slots):
    """Handle food ordering with price calculation"""
    try:
        # Extract slots
        dish_name = slots['DishName']['value']['interpretedValue']
        quantity = int(slots['Quantity']['value']['interpretedValue'])
        
        # Handle customizations
        customizations = []
        if slots.get('Customization') and slots['Customization']:
            if isinstance(slots['Customization']['value'], dict):
                customizations = [slots['Customization']['value']['interpretedValue']]
            elif isinstance(slots['Customization']['value'], list):
                customizations = [item['interpretedValue'] for item in slots['Customization']['value']]
        
        print(f"Processing order: {quantity}x {dish_name}, Customizations: {customizations}")
        
        # Calculate pricing
        pricing_result = pricing_service.calculate_order_total(dish_name, quantity, customizations)
        
        if not pricing_result['success']:
            return create_price_not_found_response(event, pricing_result)
        
        # Store order in DynamoDB
        order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.datetime.now().isoformat()
        
        order_item = {
            'OrderID': order_id,
            'Timestamp': timestamp,
            'DishName': dish_name,
            'Quantity': quantity,
            'BasePrice': Decimal(str(pricing_result['base_price'])),
            'TotalPrice': Decimal(str(pricing_result['final_total'])),
            'Status': 'Pending'
        }
        
        if customizations:
            order_item['Customizations'] = customizations
        
        if pricing_result['customization_charge'] > 0:
            order_item['CustomizationCharge'] = Decimal(str(pricing_result['customization_charge']))
        
        # Save to DynamoDB
        orders_table = dynamodb.Table(ORDERS_TABLE)
        orders_table.put_item(Item=order_item)
        
        # Send notification
        send_order_notification(order_item, pricing_result)
        
        # Create confirmation message
        response_message = create_order_confirmation_message(pricing_result)
        
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': 'OrderFood', 'state': 'Fulfilled'}
            },
            'messages': [{
                'contentType': 'PlainText',
                'content': response_message
            }]
        }
        
    except Exception as e:
        print(f"Error in handle_order_food: {e}")
        return create_error_response(event, "Error processing your order")


def handle_get_price(event, slots):
    """Handle price inquiry requests"""
    try:
        dish_name = slots['DishName']['value']['interpretedValue']
        
        price = pricing_service.find_price(dish_name)
        
        if price is None:
            message = f"Sorry, I couldn't find pricing for '{dish_name}'. Please try a different dish name or ask to see our menu."
        else:
            message = f"{dish_name} costs ${price:.2f}."
        
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': 'GetPrice', 'state': 'Fulfilled'}
            },
            'messages': [{
                'contentType': 'PlainText',
                'content': message
            }]
        }
        
    except Exception as e:
        print(f"Error in handle_get_price: {e}")
        return create_error_response(event, "Error getting price information")


def handle_check_menu(event, slots):
    """Handle menu viewing requests"""
    try:
        # Get a sample of popular items with prices
        popular_items = [
            ("Sweet & Sour Chicken", 13.25),
            ("Beef with Broccoli", 14.25),
            ("Kung Pao Chicken", 13.25),
            ("Fried Rice", 10.00),
            ("Chow Mein", 10.00),
            ("Orange Chicken", 13.25)
        ]
        
        menu_text = "Here are some popular items from our menu:\\n"
        for item, price in popular_items:
            menu_text += f"• {item}: ${price:.2f}\\n"
        
        menu_text += "\\nWhat would you like to order or check the price for?"
        
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': 'CheckMenu', 'state': 'Fulfilled'}
            },
            'messages': [{
                'contentType': 'PlainText',
                'content': menu_text
            }]
        }
        
    except Exception as e:
        print(f"Error in handle_check_menu: {e}")
        return create_error_response(event, "Error displaying menu")


def create_order_confirmation_message(pricing_result):
    """Create order confirmation message with pricing"""
    message = f"Order confirmed: {pricing_result['quantity']}x {pricing_result['dish_name']}"
    
    if pricing_result['customization_details']:
        customizations = [detail.split(':')[0] for detail in pricing_result['customization_details']]
        message += f" with {', '.join(customizations)}"
    
    message += f". Total: ${pricing_result['final_total']:.2f}"
    
    if pricing_result['customization_charge'] > 0:
        total_custom_charge = pricing_result['customization_charge'] * pricing_result['quantity']
        message += f" (includes ${total_custom_charge:.2f} for customizations)"
    
    message += ". Your order has been placed successfully!"
    
    return message


def send_order_notification(order_item, pricing_result):
    """Send notification with pricing information"""
    try:
        customization_text = ""
        if order_item.get('Customizations'):
            customization_text = f", 特殊要求: {', '.join(order_item['Customizations'])}"
        
        notification_message = f"菜品: {order_item['DishName']}, 数量: {order_item['Quantity']}, 价格: ${pricing_result['final_total']:.2f}{customization_text}"
        
        payload = {
            "default": "New order with pricing",
            "APNS_SANDBOX": json.dumps({
                "aps": {
                    "alert": {
                        "title": f"New Order - ${pricing_result['final_total']:.2f}",
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
        
        print("Notification sent successfully")
        
    except Exception as e:
        print(f"Error sending notification: {e}")


def create_price_not_found_response(event, pricing_result):
    """Handle case when price is not found"""
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {
                'name': event['sessionState']['intent']['name'],
                'state': 'Failed'
            }
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': f"I couldn't find pricing for '{pricing_result['dish_name']}'. Please check our menu or try a different dish name. You can ask me 'what's on the menu' to see popular items."
        }]
    }


def create_error_response(event, error_msg):
    """Create error response"""
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {
                'name': event['sessionState']['intent']['name'] if 'sessionState' in event else 'Unknown',
                'state': 'Failed'
            }
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': "An error occurred while processing your request. Please try again."
        }]
    }


def handle_unknown_intent(event, intent_name):
    """Handle unknown intents"""
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'}
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': "I can help you place orders, check prices, or view our menu. What would you like to do?"
        }]
    }