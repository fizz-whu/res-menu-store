#!/usr/bin/env python3
"""
Restaurant Pricing System for Bot Integration
Handles menu pricing, price lookups, and order calculations
"""

import json
import boto3
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Union
from difflib import SequenceMatcher


class PricingService:
    def __init__(self, menu_data_path: str = None, dynamodb_table: str = "cnres_menu_pricing"):
        self.dynamodb_table = dynamodb_table
        self.dynamodb = boto3.resource('dynamodb')
        self.menu_data = {}
        self.price_index = {}
        
        if menu_data_path:
            self.load_menu_data(menu_data_path)
        
        self.setup_pricing_database()
    
    def load_menu_data(self, menu_data_path: str):
        """Load menu data from JSON file"""
        try:
            with open(menu_data_path, 'r', encoding='utf-8') as f:
                self.menu_data = json.load(f)
            
            # Build price index for fast lookups
            self.build_price_index()
            print(f"✅ Loaded menu data with {len(self.price_index)} items")
            
        except Exception as e:
            print(f"❌ Error loading menu data: {e}")
    
    def build_price_index(self):
        """Build searchable index of all menu items with prices"""
        self.price_index = {}
        
        menu_sections = self.menu_data.get('menu_sections', {})
        
        for section_name, section_data in menu_sections.items():
            if isinstance(section_data, list):
                # Standard menu section with items list
                for item in section_data:
                    if isinstance(item, dict) and 'price' in item:
                        self.add_item_to_index(item, section_name)
            
            elif isinstance(section_data, dict):
                # Special sections like family_dinner
                if 'hong_kong_style' in section_data:
                    # Family dinner pricing
                    hk_style = section_data['hong_kong_style']
                    self.price_index['hong kong style family dinner'] = {
                        'price_per_person': hk_style.get('price_per_person', 14.75),
                        'minimum_persons': hk_style.get('minimum_persons', 2),
                        'section': 'family_dinner',
                        'type': 'per_person'
                    }
                
                if 'peking_style' in section_data:
                    peking_style = section_data['peking_style']
                    self.price_index['peking style family dinner'] = {
                        'price_per_person': peking_style.get('price_per_person', 15.75),
                        'minimum_persons': peking_style.get('minimum_persons', 2),
                        'section': 'family_dinner',
                        'type': 'per_person'
                    }
    
    def add_item_to_index(self, item: Dict, section: str):
        """Add individual menu item to search index"""
        name_en = item.get('name_en', '').lower()
        name_zh = item.get('name_zh', '')
        price = item.get('price')
        
        # Handle different price formats
        if isinstance(price, str):
            # Extract numeric price from strings like "14.00 Whole 26.00"
            price_match = re.search(r'(\d+\.?\d*)', price)
            if price_match:
                numeric_price = float(price_match.group(1))
            else:
                numeric_price = 0.0
            
            # Store full price string for complex pricing
            full_price_info = price
        else:
            numeric_price = float(price) if price else 0.0
            full_price_info = numeric_price
        
        # Create search entries
        item_data = {
            'name_en': item.get('name_en', ''),
            'name_zh': name_zh,
            'price': numeric_price,
            'full_price_info': full_price_info,
            'section': section,
            'id': item.get('id'),
            'type': 'menu_item'
        }
        
        # Index by English name
        if name_en:
            self.price_index[name_en] = item_data
            
            # Also index without common words for better matching
            simplified_name = self.simplify_dish_name(name_en)
            if simplified_name != name_en:
                self.price_index[simplified_name] = item_data
        
        # Index by Chinese name if available
        if name_zh:
            self.price_index[name_zh] = item_data
    
    def simplify_dish_name(self, name: str) -> str:
        """Simplify dish name for better matching"""
        # Remove common words and simplify
        name = name.lower()
        common_words = ['w/', 'with', 'special', 'deluxe', 'supreme', 'style', 'sauce']
        
        for word in common_words:
            name = name.replace(f' {word} ', ' ')
            name = name.replace(f' {word}', '')
            name = name.replace(f'{word} ', '')
        
        # Clean up extra spaces
        name = ' '.join(name.split())
        return name
    
    def setup_pricing_database(self):
        """Setup DynamoDB table for pricing if needed"""
        try:
            table = self.dynamodb.Table(self.dynamodb_table)
            table.load()
            print(f"✅ Pricing table '{self.dynamodb_table}' exists")
        except:
            print(f"⚠️  Pricing table '{self.dynamodb_table}' not found")
            # In production, you would create the table here
    
    def find_price(self, dish_name: str) -> Optional[Dict]:
        """Find price for a dish name using fuzzy matching"""
        dish_name_lower = dish_name.lower()
        
        # Exact match first
        if dish_name_lower in self.price_index:
            return self.price_index[dish_name_lower]
        
        # Try simplified name
        simplified = self.simplify_dish_name(dish_name)
        if simplified in self.price_index:
            return self.price_index[simplified]
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        threshold = 0.6  # Minimum similarity score
        
        for indexed_name, item_data in self.price_index.items():
            # Check similarity with indexed name
            score = SequenceMatcher(None, dish_name_lower, indexed_name).ratio()
            
            # Also check similarity with original English name
            if item_data.get('name_en'):
                en_score = SequenceMatcher(None, dish_name_lower, item_data['name_en'].lower()).ratio()
                score = max(score, en_score)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = item_data
        
        return best_match
    
    def calculate_order_total(self, dish_name: str, quantity: int, customizations: List[str] = None) -> Dict:
        """Calculate total price for an order item"""
        # Find base price
        price_info = self.find_price(dish_name)
        
        if not price_info:
            return {
                'success': False,
                'error': f'Price not found for "{dish_name}"',
                'dish_name': dish_name,
                'quantity': quantity
            }
        
        base_price = price_info['price']
        
        # Handle special pricing (like family dinners)
        if price_info.get('type') == 'per_person':
            if quantity < price_info.get('minimum_persons', 2):
                quantity = price_info.get('minimum_persons', 2)
            total_price = base_price * quantity
            pricing_note = f"${base_price:.2f} per person, minimum {price_info.get('minimum_persons', 2)} persons"
        else:
            total_price = base_price * quantity
            pricing_note = f"${base_price:.2f} per item"
        
        # Apply customization charges if any
        customization_charge = 0.0
        customization_details = []
        
        if customizations:
            for custom in customizations:
                charge = self.get_customization_charge(custom)
                if charge > 0:
                    customization_charge += charge
                    customization_details.append(f"{custom}: +${charge:.2f}")
        
        final_total = total_price + (customization_charge * quantity)
        
        return {
            'success': True,
            'dish_name': dish_name,
            'matched_name': price_info.get('name_en', dish_name),
            'quantity': quantity,
            'base_price': base_price,
            'total_base': total_price,
            'customization_charge': customization_charge,
            'customization_details': customization_details,
            'final_total': round(final_total, 2),
            'pricing_note': pricing_note,
            'section': price_info.get('section'),
            'full_price_info': price_info.get('full_price_info')
        }
    
    def get_customization_charge(self, customization: str) -> float:
        """Get additional charge for customizations"""
        # Define customization charges
        customization_charges = {
            'extra spicy': 0.0,  # Free
            'no msg': 0.0,      # Free
            'extra sauce': 0.50,
            'extra vegetables': 1.00,
            'extra meat': 2.00,
            'well done': 0.0,   # Free
            'extra rice': 1.75,
            'no onions': 0.0,   # Free
            'no garlic': 0.0,   # Free
        }
        
        custom_lower = customization.lower()
        
        # Check for exact matches first
        if custom_lower in customization_charges:
            return customization_charges[custom_lower]
        
        # Check for partial matches
        for key, charge in customization_charges.items():
            if key in custom_lower or custom_lower in key:
                return charge
        
        # Default: no charge for unknown customizations
        return 0.0
    
    def get_menu_section_prices(self, section: str) -> List[Dict]:
        """Get all items and prices for a menu section"""
        section_items = []
        
        for item_data in self.price_index.values():
            if item_data.get('section') == section and item_data.get('type') == 'menu_item':
                section_items.append({
                    'name': item_data.get('name_en', ''),
                    'chinese_name': item_data.get('name_zh', ''),
                    'price': item_data.get('price', 0),
                    'full_price_info': item_data.get('full_price_info')
                })
        
        # Sort by price
        section_items.sort(key=lambda x: x['price'])
        return section_items
    
    def store_pricing_to_dynamodb(self):
        """Store pricing data to DynamoDB for production use"""
        try:
            table = self.dynamodb.Table(self.dynamodb_table)
            
            # Batch write pricing data
            with table.batch_writer() as batch:
                for dish_name, price_info in self.price_index.items():
                    # Convert Decimal for DynamoDB
                    item = {
                        'dish_name': dish_name,
                        'price': Decimal(str(price_info['price'])),
                        'name_en': price_info.get('name_en', ''),
                        'name_zh': price_info.get('name_zh', ''),
                        'section': price_info.get('section', ''),
                        'full_price_info': str(price_info.get('full_price_info', '')),
                        'item_type': price_info.get('type', 'menu_item')
                    }
                    batch.put_item(Item=item)
            
            print(f"✅ Stored {len(self.price_index)} items to DynamoDB")
            
        except Exception as e:
            print(f"❌ Error storing to DynamoDB: {e}")


def create_pricing_enhanced_lambda():
    """Create enhanced lambda function with pricing integration"""
    
    lambda_code = '''
import boto3
import json
import datetime
from decimal import Decimal

# Import our pricing service
from pricing_service import PricingService

# DynamoDB table names
ORDERS_TABLE = "cnres0_orders"
PRICING_TABLE = "cnres_menu_pricing"

# SNS endpoint ARN
endpoint_arn = "arn:aws:sns:us-west-2:495599767527:endpoint/APNS_SANDBOX/CnResOrderDisplayNotificationDev/e9792aab-7449-3d7b-98ac-2ebf2ef919fc"

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns', region_name='us-west-2')

# Initialize pricing service
pricing_service = PricingService(dynamodb_table=PRICING_TABLE)

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    
    try:
        # Extract intent and slots
        intent_name = event['sessionState']['intent']['name']
        slots = event['sessionState']['intent']['slots']
        
        if intent_name == 'OrderFood':
            return handle_order_food(event, slots)
        elif intent_name == 'GetPrice':
            return handle_get_price(event, slots)
        else:
            return handle_unknown_intent(event, intent_name)
            
    except Exception as e:
        print("Error:", e)
        return create_error_response(event, str(e))

def handle_order_food(event, slots):
    """Handle food ordering with price calculation"""
    # Extract slots
    dish_name = slots['DishName']['value']['interpretedValue']
    quantity = int(slots['Quantity']['value']['interpretedValue'])
    
    # Handle optional Customization slot
    customizations = []
    if slots.get('Customization') and slots['Customization']:
        if isinstance(slots['Customization']['value'], dict):
            customizations = [slots['Customization']['value']['interpretedValue']]
        elif isinstance(slots['Customization']['value'], list):
            customizations = [item['interpretedValue'] for item in slots['Customization']['value']]
    
    print(f"Order: {quantity}x {dish_name}, Customizations: {customizations}")
    
    # Calculate pricing
    pricing_result = pricing_service.calculate_order_total(dish_name, quantity, customizations)
    
    if not pricing_result['success']:
        return create_price_not_found_response(event, pricing_result)
    
    # Store order in DynamoDB with pricing
    order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.datetime.now().isoformat()
    
    order_item = {
        'OrderID': order_id,
        'Timestamp': timestamp,
        'DishName': dish_name,
        'MatchedDishName': pricing_result['matched_name'],
        'Quantity': quantity,
        'BasePrice': Decimal(str(pricing_result['base_price'])),
        'CustomizationCharge': Decimal(str(pricing_result['customization_charge'])),
        'TotalPrice': Decimal(str(pricing_result['final_total'])),
        'Status': 'Pending'
    }
    
    if customizations:
        order_item['Customizations'] = customizations
        order_item['CustomizationDetails'] = pricing_result['customization_details']
    
    # Save to DynamoDB
    orders_table = dynamodb.Table(ORDERS_TABLE)
    orders_table.put_item(Item=order_item)
    
    # Send notification
    send_order_notification(order_item, pricing_result)
    
    # Create response message with pricing
    response_message = create_order_confirmation_message(pricing_result)
    
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': 'OrderFood',
                'state': 'Fulfilled'
            }
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': response_message
        }]
    }

def handle_get_price(event, slots):
    """Handle price inquiry requests"""
    dish_name = slots['DishName']['value']['interpretedValue']
    
    pricing_result = pricing_service.find_price(dish_name)
    
    if not pricing_result:
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': 'GetPrice', 'state': 'Fulfilled'}
            },
            'messages': [{
                'contentType': 'PlainText',
                'content': f"Sorry, I couldn't find pricing for '{dish_name}'. Please try a different dish name or ask to see our menu."
            }]
        }
    
    # Create price response
    if pricing_result.get('type') == 'per_person':
        price_message = f"{pricing_result['name_en']} costs ${pricing_result['price']:.2f} per person (minimum {pricing_result.get('minimum_persons', 2)} persons)."
    else:
        price_message = f"{pricing_result['name_en']} costs ${pricing_result['price']:.2f}."
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': 'GetPrice', 'state': 'Fulfilled'}
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': price_message
        }]
    }

def create_order_confirmation_message(pricing_result):
    """Create order confirmation message with pricing details"""
    base_message = f"Order confirmed: {pricing_result['quantity']}x {pricing_result['matched_name']}"
    
    if pricing_result['customization_details']:
        base_message += f" with {', '.join([detail.split(':')[0] for detail in pricing_result['customization_details']])}"
    
    base_message += f". Total: ${pricing_result['final_total']:.2f}"
    
    if pricing_result['customization_charge'] > 0:
        base_message += f" (includes ${pricing_result['customization_charge'] * pricing_result['quantity']:.2f} for customizations)"
    
    base_message += ". Your order has been placed successfully!"
    
    return base_message

def send_order_notification(order_item, pricing_result):
    """Send notification with pricing information"""
    customization_text = ""
    if order_item.get('Customizations'):
        customization_text = f", 特殊要求: {', '.join(order_item['Customizations'])}"
    
    notification_message = f"菜品: {pricing_result['matched_name']}, 数量: {order_item['Quantity']}, 价格: ${pricing_result['final_total']:.2f}{customization_text}"
    
    payload = {
        "default": "New order with pricing",
        "APNS_SANDBOX": json.dumps({
            "aps": {
                "alert": {
                    "title": "New Order - Total: $" + str(pricing_result['final_total']),
                    "body": notification_message
                },
                "sound": "default",
                "badge": 1
            }
        })
    }
    
    try:
        sns_client.publish(
            TargetArn=endpoint_arn,
            MessageStructure='json',
            Message=json.dumps(payload)
        )
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
            'content': f"I couldn't find pricing for '{pricing_result['dish_name']}'. Please check the menu or try a different dish name."
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
            'content': "I'm not sure how to help with that. You can place an order or ask for prices."
        }]
    }
'''
    
    return lambda_code


def main():
    """Demo the pricing system"""
    print("🍽️  Restaurant Pricing System Demo")
    print("=" * 50)
    
    # Initialize pricing service with menu data
    menu_data_path = "/home/fizz/work/res-menu-store/data/CnRes001/extracted_menu_data.json"
    pricing_service = PricingService(menu_data_path)
    
    # Demo price lookups
    test_dishes = [
        "Sweet & Sour Chicken",
        "Beef with Broccoli", 
        "Kung Pao Chicken",
        "Walnut Prawns",
        "Hong Kong Style Family Dinner"
    ]
    
    print("\\n🔍 Price Lookup Tests:")
    print("-" * 30)
    
    for dish in test_dishes:
        result = pricing_service.calculate_order_total(dish, 2, ["extra spicy", "no MSG"])
        if result['success']:
            print(f"✅ {dish}:")
            print(f"   Matched: {result['matched_name']}")
            print(f"   Price: ${result['base_price']:.2f} each")
            print(f"   Total for 2: ${result['final_total']:.2f}")
            if result['customization_details']:
                print(f"   Customizations: {', '.join(result['customization_details'])}")
        else:
            print(f"❌ {dish}: {result['error']}")
        print()


if __name__ == "__main__":
    main()