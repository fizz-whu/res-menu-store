import boto3
import json
import csv
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MenuDynamoDBManager:
    """
    Manages menu items in DynamoDB for restaurant ordering system.
    Handles CRUD operations, price lookups, and order total calculations.
    """
    
    def __init__(self, table_name: str = "RestaurantMenu", region_name: str = "us-east-1"):
        """
        Initialize DynamoDB manager
        
        Args:
            table_name: Name of the DynamoDB table
            region_name: AWS region name
        """
        self.table_name = table_name
        self.region_name = region_name
        
        # Initialize DynamoDB resources
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        
    def create_table(self):
        """
        Create DynamoDB table with optimized schema for menu items
        
        Table Schema:
        - item_id (Primary Key): Unique identifier for each menu item
        - category (GSI): Menu category (SEAFOOD, VEGETABLES, etc.)
        - english_name: English name of the dish
        - chinese_name: Chinese name of the dish  
        - price: Price in USD (Decimal for precision)
        - description: Optional description
        - available: Boolean indicating if item is available
        - created_at: Timestamp when item was created
        - updated_at: Timestamp when item was last updated
        - tags: List of searchable tags for the item
        """
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'item_id',
                        'KeyType': 'HASH'  # Primary key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'item_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'category',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'english_name',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'category-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'category',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'english-name-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'english_name',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            logger.info(f"Table {self.table_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            return False

    def generate_item_id(self, english_name: str, category: str) -> str:
        """Generate unique item ID from English name and category"""
        # Clean and format the name
        clean_name = english_name.upper().replace(' ', '_').replace('/', '_').replace('&', 'AND')
        clean_category = category.upper().replace(' ', '_')
        return f"{clean_category}_{clean_name}"

    def normalize_price(self, price_str: str) -> Decimal:
        """Convert price string to Decimal for DynamoDB storage"""
        try:
            # Remove $ sign and extra text, convert to Decimal
            clean_price = price_str.replace('$', '').split()[0]
            return Decimal(clean_price)
        except:
            return Decimal('0.00')

    def load_menu_from_csv(self, csv_file_path: str) -> bool:
        """
        Load menu items from CSV file into DynamoDB
        
        Args:
            csv_file_path: Path to the menu CSV file
            
        Returns:
            bool: Success status
        """
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                items_loaded = 0
                current_time = datetime.utcnow().isoformat()
                
                for row in csv_reader:
                    try:
                        category = row['Category'].strip()
                        chinese_name = row['Item Chinese Name'].strip()
                        english_name = row['Item English Name'].strip()
                        price_str = row['Price'].strip()
                        
                        # Generate unique item ID
                        item_id = self.generate_item_id(english_name, category)
                        
                        # Prepare item for DynamoDB
                        item = {
                            'item_id': item_id,
                            'category': category,
                            'english_name': english_name,
                            'chinese_name': chinese_name,
                            'price': self.normalize_price(price_str),
                            'price_display': price_str,  # Keep original format for display
                            'available': True,
                            'created_at': current_time,
                            'updated_at': current_time,
                            'tags': self._generate_tags(english_name, category)
                        }
                        
                        # Save to DynamoDB
                        self.table.put_item(Item=item)
                        items_loaded += 1
                        
                        if items_loaded % 10 == 0:
                            logger.info(f"Loaded {items_loaded} items...")
                            
                    except Exception as e:
                        logger.error(f"Error loading item {english_name}: {str(e)}")
                        continue
                
                logger.info(f"Successfully loaded {items_loaded} menu items to DynamoDB")
                return True
                
        except Exception as e:
            logger.error(f"Error loading menu from CSV: {str(e)}")
            return False

    def load_menu_from_hardcoded(self) -> bool:
        """
        Load menu items from the hard-coded MENU_PRICES dictionary
        
        Returns:
            bool: Success status
        """
        # Hard-coded menu prices from improved_dish_analyzer.py
        MENU_PRICES = {
            "SHRIMP W/ CASHEW": "14.50",
            "SHRIMP W/ SNOW PEAS": "14.50", 
            "SHRIMP W/ DOUBLE MUSHROOMS": "14.50",
            "SHRIMP W/ LOBSTER SAUCE": "14.50",
            "SUPERMEN SWEET & SOUR SHRIMP": "14.50",
            "KUNG PAO SHRIMP": "14.50",
            "CURRY SHRIMP": "14.50",
            "SEAFOOD DELUXE": "14.50",
            "CLAMS W/ GINGER SCALLIONS": "14.50",
            "CLAMS W/ BLACK BEAN SAUCE": "14.50",
            "BRAISED FISH FILLET": "14.50",
            "FISH FILLET W/ BLACK BEAN SAUCE": "14.50",
            "SWEET AND SOUR WHOLE FISH": "22.00",
            "STEAMED WHOLE FISH": "20.00",
            "FRESH VEGETABLES DELUXE": "11.00",
            "SNOW PEAS W/ WATER CHESTNUTS": "11.00",
            "EGGPLANT W/ GARLIC SAUCE": "11.00",
            "BROCCOLI W/ OYSTER SAUCE": "11.00",
            "DOUBLE MUSHROOM W/ OYSTER SAUCE": "11.00",
            "VEGETARIAN'S SPECIAL": "11.00",
            "BRAISED BEAN CAKE": "11.00",
            "MIXED VEGETABLES W/ BEAN CAKE": "11.00",
            "HOUSE SPECIAL BEAN CAKE": "12.00",
            "KUNG PAO TO FU": "12.00",
            "BARBECUED PORK WONTON SOUP": "10.50",
            "BEEF WONTON SOUP": "10.50",
            "CHICKEN WONTON SOUP": "10.50",
            "ROASTED DUCK WONTON SOUP": "10.50",
            "SHRIMP WONTON SOUP": "10.50",
            "BARBECUED PORK NOODLE SOUP": "9.75",
            "BEEF NOODLE SOUP": "9.75",
            "CHICKEN NOODLE SOUP": "9.75",
            "ROASTED DUCK NOODLE SOUP": "10.50",
            "SHRIMP NOODLE SOUP": "10.50",
            "HONG KONG STYLE (MINIMUM FOR 2 PERSON)": "15.75 PER PERSON",
            "PEKING STYLE (MINIMUM FOR 2 PERSON)": "15.75 PER PERSON",
            "SPICY SALT PEPPER SHRIMP": "16.25",
            "MINCED CHICKEN W/ LETTUCE CUP": "13.25",
            "WALNUT PRAWNS": "16.25",
            "RAINBOW FISH FILLET": "13.25",
            "ORANGE PEEL BEEF": "13.25",
            "ORANGE PEEL CHICKEN": "13.25",
            "GINGER GREEN ONION W/ OYSTER": "13.25",
            "CRISPY FRIED OYSTER": "14.25",
            "SESAME CHICKEN": "13.25",
            "CRISPY FRIED SQUID W/ SPICY PEPPER": "14.25",
            "FRIED TOFU W/ GREEN BEAN IN DRY SPICY GARLIC": "12.75",
            "EGGPLANT W/ CHICKEN, SHRIMP IN SPECIAL SAUCE": "14.75",
            "SPICY SALT PEPPER PORK CHOP": "13.25",
            "YELLOW ONION PORK CHOP": "13.25",
            "SPICY SALT PEPPER CHICKEN WINGS(10)": "14.25",
            "GENERALS CHICKEN WINGS(10)": "14.25",
            "HONEY GLAZED BARBECUED PORK": "10.75",
            "CRISPY FRIED PRAWNS (10)": "14.75",
            "GOLDEN POT STICKERS (6)": "9.00",
            "SPRING EGG ROLLS (4)": "9.00",
            "CHICKEN SALAD": "8.75",
            "WONTON SOUP": "9.00",
            "MINCED BEEF W/ EGG WHITE SOUP": "9.00",
            "MIXED VEGETABLES SOUP": "9.00",
            "SEAWEED W/ EGG FLOWER SOUP": "9.00",
            "SEAFOOD W/ BEAN CAKE SOUP": "10.00",
            "WOR WONTON SOUP": "10.50",
            "CHICKEN W/ CORN SOUP": "11.50",
            "ALMOND CHICKEN": "13.25",
            "SWEET & SOUR CHICKEN": "13.25",
            "LEMON CHICKEN": "13.25",
            "CHICKEN W/ DOUBLE MUSHROOMS": "13.25",
            "RAINBOW CHICKEN": "13.25",
            "CHICKEN W/ BLACK BEAN SAUCE": "13.25",
            "CURRY CHICKEN": "13.25",
            "KUNG PAO CHICKEN": "13.25",
            "CHICKEN W/ BROCCOLI": "13.25",
            "ROASTED DUCK HALF": "14.00",
            "ROASTED DUCK WHOLE": "26.00",
            "FRIED CHICKEN HALF": "12.00",
            "CHICKEN W/ MIXED VEGETABLES": "13.25",
            "CANTONESE STYLE SPARERIBS": "13.25",
            "SPICY HOT BEAN CURD W/ MINCED PORK": "13.25",
            "SUCCULENT SPICY PORK W/ GARLIC SAUCE": "13.25",
            "SUPERMEN SWEET AND SOUR PORK": "13.25",
            "MU SHU PORK (FOUR PAN CAKE)": "13.25",
            "SPARERIBS W/ BLACK BEAN SAUCE": "13.25",
            "BARBECUED PORK W/ BEAN CAKE": "13.25",
            "BARBECUED PORK W/ MIXED VEGETABLES": "13.25",
            "PEPPING SPICY BEEF": "14.25",
            "MONGOLIAN BEEF": "14.25",
            "CURRY BEEF": "14.25",
            "BEEF W/ BLACK BEAN SAUCE": "14.25",
            "BEEF W/ BROCCOLI": "14.25",
            "BEEF W/ OYSTER SAUCE": "14.25",
            "BEEF W/ SNOW PEAS": "14.25",
            "BEEF W/ MIXED VEGETABLES": "14.25",
            "HOUSE SPECIAL CHOW MEIN": "12.25",
            "SHRIMP CHOW MEIN": "10.75",
            "CHICKEN CHOW MEIN": "10.00",
            "BEEF W/ TOMATO CHOW MEIN": "10.50",
            "HOUSE SPECIAL PAN FRIED NOODLES": "13.00",
            "SEAFOOD PAN FRIED NOODLES": "13.00",
            "BEEF W/ TENDER GREEN PAN FRIED NOODLES": "11.25",
            "BEEF W/ BROCCOLI PAN FRIED NOODLES": "11.25",
            "BEEF W/ BLACK BEAN SAUCE PAN FRIED NOODLES": "11.25",
            "CHICKEN W/ TENDER GREEN PAN FRIED NOODLES": "11.25",
            "CHICKEN W/ BLACK BEAN SAUCE PAN FRIED NOODLES": "11.25",
            "MIXED VEGETABLE W/ TENDER GREEN PAN FRIED NOODLES": "12.25",
            "SHRIMP W/ MIXED VEGETABLE PAN FRIED NOODLES": "12.25",
            "SHRIMP W/ BLACK BEAN SAUCE PAN FRIED NOODLES": "12.25",
            "HOUSE SPECIAL FRIED RICE": "12.00",
            "SHRIMP FRIED RICE": "11.00",
            "YANG CHOW FRIED RICE": "11.00",
            "BARBECUED PORK FRIED RICE": "10.00",
            "CHICKEN FRIED RICE": "10.00",
            "BEEF FRIED RICE": "10.00",
            "FRESH VEGETABLES FRIED RICE": "10.00",
            "CHICKEN W/ SALTED FISH FRIED RICE": "12.25",
            "STEAMED RICE": "1.75",
            "HOUSE SPECIAL CHOW FUN": "13.00",
            "SEAFOOD CHOW FUN": "13.00",
            "SHRIMP W/ TENDER GREEN CHOW FUN": "11.50",
            "BEEF W/ BLACK BEAN SAUCE CHOW FUN": "11.00",
            "BEEF W/ BEAN SPROUT CHOW FUN": "11.00",
            "SINGAPORE STYLE CHOW RICE NOODLE": "12.00",
            "HOUSE SPECIAL ON RICE": "12.00",
            "SEAFOOD ON RICE": "12.00",
            "SHRIMP W/ MIXED VEGETABLES ON RICE": "10.00",
            "SHRIMP W/ SCRAMBLED EGG ON RICE": "10.00",
            "SHRIMP W/ BLACK BEAN SAUCE ON RICE": "10.00",
            "B.B.Q. PORK W/ BEAN CAKE ON RICE": "10.00",
            "CHICKEN W/ TENDER GREEN ON RICE": "10.00",
            "BEEF W/ BROCCOLI ON RICE": "10.00",
            "BEEF W/ OYSTER SAUCE ON RICE": "10.00",
            "BEEF W/ GINGER & SCALLIONS ON RICE": "10.00",
            "BEEF W/ TENDER GREEN ON RICE": "10.00",
            "CHICKEN W/ BLACK BEAN SAUCE ON RICE": "10.00",
            "CHICKEN W/ MIXED VEGETABLES ON RICE": "10.00",
            "CHICKEN W/ CURRY ON RICE": "10.00",
            "BEEF STEW W/ CURRY ON RICE": "10.00",
            "BEEF STEW W/ ORIGINAL JUICE ON RICE": "10.00",
            "SPARERIBS W/ BLACK BEAN SAUCE ON RICE": "10.00",
            "SPARERIBS W/ BEAN CAKE ON RICE": "10.00",
            "ROASTED DUCK ON RICE": "11.25",
            "ROASTED DUCK W/ BEAN CAKE ON RICE": "11.25",
            "TSING TAO": "5.25",
            "HEINEKEN": "5.25",
            "CORONA": "5.25",
            "DEEP-FRIED BANANA": "4.00",
            "DRINKS": "1.85"
        }
        
        try:
            items_loaded = 0
            current_time = datetime.utcnow().isoformat()
            
            for english_name, price_str in MENU_PRICES.items():
                try:
                    # Determine category based on item name
                    category = self._determine_category(english_name)
                    
                    # Generate unique item ID
                    item_id = self.generate_item_id(english_name, category)
                    
                    # Prepare item for DynamoDB
                    item = {
                        'item_id': item_id,
                        'category': category,
                        'english_name': english_name,
                        'chinese_name': '',  # Not available in hard-coded data
                        'price': self.normalize_price(price_str),
                        'price_display': f"${price_str}",
                        'available': True,
                        'created_at': current_time,
                        'updated_at': current_time,
                        'tags': self._generate_tags(english_name, category)
                    }
                    
                    # Save to DynamoDB
                    self.table.put_item(Item=item)
                    items_loaded += 1
                    
                    if items_loaded % 20 == 0:
                        logger.info(f"Loaded {items_loaded} items...")
                        
                except Exception as e:
                    logger.error(f"Error loading item {english_name}: {str(e)}")
                    continue
            
            logger.info(f"Successfully loaded {items_loaded} menu items from hard-coded data to DynamoDB")
            return True
            
        except Exception as e:
            logger.error(f"Error loading menu from hard-coded data: {str(e)}")
            return False

    def _determine_category(self, english_name: str) -> str:
        """Determine category based on item name for hard-coded data"""
        name_upper = english_name.upper()
        
        if any(word in name_upper for word in ['SHRIMP', 'CLAMS', 'FISH', 'SEAFOOD', 'PRAWNS']):
            return 'SEAFOOD'
        elif any(word in name_upper for word in ['VEGETABLES', 'EGGPLANT', 'BROCCOLI', 'SNOW PEAS', 'BEAN CAKE', 'TOFU']):
            return 'VEGETABLES'
        elif any(word in name_upper for word in ['WONTON SOUP', 'NOODLE SOUP']):
            return 'WONTON, NOODLE SOUP'
        elif 'FAMILY DINNER' in name_upper or 'STYLE' in name_upper:
            return 'FAMILY DINNER'
        elif any(word in name_upper for word in ['OYSTER', 'SQUID', 'WALNUT', 'ORANGE PEEL', 'SESAME', 'SALT PEPPER']):
            return 'HOUSE SPECIAL'
        elif any(word in name_upper for word in ['EGG ROLLS', 'POT STICKERS', 'PRAWNS', 'SALAD']):
            return 'APPETIZERS'
        elif 'SOUP' in name_upper:
            return 'SOUP'
        elif any(word in name_upper for word in ['CHICKEN', 'DUCK', 'FRIED CHICKEN']):
            return 'FOWLS'
        elif any(word in name_upper for word in ['PORK', 'SPARERIBS']):
            return 'PORK'
        elif 'BEEF' in name_upper:
            return 'BEEF'
        elif 'CHOW MEIN' in name_upper:
            return 'CHOW MEIN'
        elif 'PAN FRIED NOODLES' in name_upper:
            return 'HONG KONG STYLE PAN FRIED NOODLE'
        elif 'FRIED RICE' in name_upper or 'RICE' in name_upper:
            return 'FRIED RICE'
        elif 'CHOW FUN' in name_upper or 'RICE NOODLE' in name_upper:
            return 'CHOW FUN'
        elif 'ON RICE' in name_upper:
            return 'RICE PLATE'
        elif any(word in name_upper for word in ['BEER', 'TAO', 'HEINEKEN', 'CORONA', 'BANANA', 'DRINKS']):
            return 'BEER & WINE'
        else:
            return 'MISCELLANEOUS'

    def _generate_tags(self, english_name: str, category: str) -> List[str]:
        """Generate searchable tags for menu item"""
        tags = []
        
        # Add category as tag
        tags.append(category.lower().replace(' ', '_'))
        
        # Add individual words from name
        words = english_name.lower().replace('w/', 'with').replace('&', 'and').split()
        tags.extend([word for word in words if len(word) > 2])
        
        # Add specific tags based on content
        name_upper = english_name.upper()
        if 'SPICY' in name_upper:
            tags.append('spicy')
        if 'SWEET' in name_upper:
            tags.append('sweet')
        if 'FRIED' in name_upper:
            tags.append('fried')
        if 'SOUP' in name_upper:
            tags.append('soup')
        if 'RICE' in name_upper:
            tags.append('rice')
        
        return list(set(tags))  # Remove duplicates

    def get_item_by_name(self, english_name: str) -> Optional[Dict]:
        """
        Get menu item by English name
        
        Args:
            english_name: English name of the dish
            
        Returns:
            Dict or None: Menu item data
        """
        try:
            response = self.table.query(
                IndexName='english-name-index',
                KeyConditionExpression='english_name = :name',
                ExpressionAttributeValues={':name': english_name}
            )
            
            items = response.get('Items', [])
            return items[0] if items else None
            
        except Exception as e:
            logger.error(f"Error getting item by name {english_name}: {str(e)}")
            return None

    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        """
        Get menu item by item ID
        
        Args:
            item_id: Unique item identifier
            
        Returns:
            Dict or None: Menu item data
        """
        try:
            response = self.table.get_item(Key={'item_id': item_id})
            return response.get('Item')
            
        except Exception as e:
            logger.error(f"Error getting item by ID {item_id}: {str(e)}")
            return None

    def search_items(self, search_term: str, category: str = None) -> List[Dict]:
        """
        Search menu items by name or tags
        
        Args:
            search_term: Term to search for
            category: Optional category filter
            
        Returns:
            List[Dict]: List of matching menu items
        """
        try:
            if category:
                # Search within specific category
                response = self.table.query(
                    IndexName='category-index',
                    KeyConditionExpression='category = :cat',
                    FilterExpression='contains(english_name, :term) OR contains(tags, :term)',
                    ExpressionAttributeValues={
                        ':cat': category,
                        ':term': search_term.lower()
                    }
                )
            else:
                # Search all items
                response = self.table.scan(
                    FilterExpression='contains(english_name, :term) OR contains(tags, :term)',
                    ExpressionAttributeValues={':term': search_term.lower()}
                )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error searching items: {str(e)}")
            return []

    def update_price(self, item_id: str, new_price: str) -> bool:
        """
        Update price of a menu item
        
        Args:
            item_id: Unique item identifier
            new_price: New price as string (e.g., "15.99")
            
        Returns:
            bool: Success status
        """
        try:
            current_time = datetime.utcnow().isoformat()
            
            self.table.update_item(
                Key={'item_id': item_id},
                UpdateExpression='SET price = :price, price_display = :display, updated_at = :time',
                ExpressionAttributeValues={
                    ':price': self.normalize_price(new_price),
                    ':display': f"${new_price}",
                    ':time': current_time
                }
            )
            
            logger.info(f"Updated price for item {item_id} to ${new_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating price for item {item_id}: {str(e)}")
            return False

    def calculate_order_total(self, order_items: List[Dict]) -> Dict:
        """
        Calculate total price for an order
        
        Args:
            order_items: List of order items with format:
                [
                    {"item_name": "Kung Pao Chicken", "quantity": 2},
                    {"item_name": "Fried Rice", "quantity": 1}
                ]
                
        Returns:
            Dict: Order calculation results with items, prices, and total
        """
        try:
            order_details = []
            subtotal = Decimal('0.00')
            items_not_found = []
            
            for order_item in order_items:
                item_name = order_item.get('item_name', '')
                quantity = int(order_item.get('quantity', 1))
                
                # Look up item in DynamoDB
                menu_item = self.get_item_by_name(item_name)
                
                if menu_item:
                    item_price = menu_item['price']
                    line_total = item_price * quantity
                    
                    order_details.append({
                        'item_name': item_name,
                        'quantity': quantity,
                        'unit_price': float(item_price),
                        'line_total': float(line_total),
                        'item_id': menu_item['item_id']
                    })
                    
                    subtotal += line_total
                else:
                    items_not_found.append(item_name)
            
            # Calculate tax (assuming 8.5% tax rate)
            tax_rate = Decimal('0.085')
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount
            
            return {
                'order_details': order_details,
                'items_not_found': items_not_found,
                'subtotal': float(subtotal),
                'tax_rate': float(tax_rate),
                'tax_amount': float(tax_amount),
                'total': float(total),
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error calculating order total: {str(e)}")
            return {
                'error': str(e),
                'order_details': [],
                'items_not_found': order_items,
                'subtotal': 0.0,
                'tax_amount': 0.0,
                'total': 0.0
            }

    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        try:
            response = self.table.scan(
                ProjectionExpression='category'
            )
            
            categories = set()
            for item in response.get('Items', []):
                categories.add(item['category'])
            
            return sorted(list(categories))
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []

    def get_items_by_category(self, category: str) -> List[Dict]:
        """Get all items in a specific category"""
        try:
            response = self.table.query(
                IndexName='category-index',
                KeyConditionExpression='category = :cat',
                ExpressionAttributeValues={':cat': category}
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error getting items by category {category}: {str(e)}")
            return []


def main():
    """Main function to demonstrate usage"""
    # Initialize manager
    manager = MenuDynamoDBManager()
    
    print("=== DynamoDB Menu Manager Demo ===")
    
    # Create table (uncomment if table doesn't exist)
    # print("Creating table...")
    # manager.create_table()
    
    # Load menu from hard-coded data
    print("Loading menu items from hard-coded data...")
    success = manager.load_menu_from_hardcoded()
    
    if success:
        print("✅ Menu loaded successfully!")
        
        # Demo: Search for items
        print("\n=== Demo: Search for chicken items ===")
        chicken_items = manager.search_items("chicken")
        for item in chicken_items[:3]:  # Show first 3
            print(f"- {item['english_name']}: ${item['price']}")
        
        # Demo: Calculate order total
        print("\n=== Demo: Calculate order total ===")
        sample_order = [
            {"item_name": "KUNG PAO CHICKEN", "quantity": 2},
            {"item_name": "BEEF W/ BROCCOLI", "quantity": 1},
            {"item_name": "STEAMED RICE", "quantity": 2}
        ]
        
        order_result = manager.calculate_order_total(sample_order)
        print(f"Order Details:")
        for detail in order_result['order_details']:
            print(f"  {detail['quantity']}x {detail['item_name']} @ ${detail['unit_price']} = ${detail['line_total']}")
        
        print(f"\nSubtotal: ${order_result['subtotal']:.2f}")
        print(f"Tax: ${order_result['tax_amount']:.2f}")
        print(f"Total: ${order_result['total']:.2f}")
        
        # Demo: Get categories
        print(f"\n=== Available Categories ===")
        categories = manager.get_all_categories()
        for category in categories:
            print(f"- {category}")
            
    else:
        print("❌ Failed to load menu items")


if __name__ == "__main__":
    main()