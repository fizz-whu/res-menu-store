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

class OptimizedMenuDynamoDBManager:
    """
    Optimized DynamoDB manager using sample names as primary keys for fast Lex bot integration.
    Uses sample values from DishType.json as the primary key for direct lookup.
    """
    
    def __init__(self, table_name: str = "RestaurantMenuOptimized", region_name: str = "us-east-1"):
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
        Create optimized DynamoDB table using sample names as primary key
        
        Table Schema:
        - sample_name (Primary Key): Sample value from DishType.json (e.g., "Kung Pao Chicken")
        - menu_english_name: Actual English name from menu.csv
        - menu_chinese_name: Chinese name from menu.csv
        - category: Menu category
        - price: Price in USD (Decimal for precision)
        - price_display: Formatted price string
        - available: Boolean indicating if item is available
        - synonyms: List of alternative names for this item
        - created_at: Timestamp when item was created
        - updated_at: Timestamp when item was last updated
        """
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'sample_name',
                        'KeyType': 'HASH'  # Primary key - sample name from DishType.json
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'sample_name',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'category',
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
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            logger.info(f"Optimized table {self.table_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            return False

    def extract_sample_values_with_synonyms(self, json_file_path: str) -> Dict[str, Dict]:
        """
        Extract sample values and their synonyms from DishType.json
        
        Args:
            json_file_path: Path to DishType.json file
            
        Returns:
            Dict: {sample_name: {synonyms: [...], chinese_synonym: "..."}}
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            sample_data = {}
            for slot_type_value in data.get('slotTypeValues', []):
                sample_value = slot_type_value.get('sampleValue', {}).get('value')
                if sample_value:
                    synonyms = []
                    chinese_synonym = ""
                    
                    # Extract synonyms
                    for synonym in slot_type_value.get('synonyms', []):
                        synonym_value = synonym.get('value', '')
                        if synonym_value:
                            synonyms.append(synonym_value)
                            # Try to identify Chinese synonym (contains Chinese characters)
                            if any('\u4e00' <= char <= '\u9fff' for char in synonym_value):
                                chinese_synonym = synonym_value
                    
                    sample_data[sample_value] = {
                        'synonyms': synonyms,
                        'chinese_synonym': chinese_synonym
                    }
            
            logger.info(f"Extracted {len(sample_data)} sample values with synonyms")
            return sample_data
            
        except Exception as e:
            logger.error(f"Error extracting sample values: {str(e)}")
            return {}

    def create_sample_to_menu_mapping(self) -> Dict[str, Dict]:
        """
        Create mapping from sample names to actual menu items using hard-coded data
        
        Returns:
            Dict: {sample_name: {menu_name: "...", price: "...", category: "..."}}
        """
        # Hard-coded menu prices for mapping
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
            "HONG KONG STYLE (MINIMUM FOR 2 PERSON)": "15.75",
            "PEKING STYLE (MINIMUM FOR 2 PERSON)": "15.75",
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
        
        # Sample name mappings (sample name -> menu name)
        SAMPLE_MAPPINGS = {
            "Kung Pao Chicken": "KUNG PAO CHICKEN",
            "Beef with Broccoli": "BEEF W/ BROCCOLI", 
            "Sweet & Sour Chicken": "SWEET & SOUR CHICKEN",
            "Fried Rice": "HOUSE SPECIAL FRIED RICE",
            "Steamed Rice": "STEAMED RICE",
            "Mongolian Beef": "MONGOLIAN BEEF",
            "Orange Peel Chicken": "ORANGE PEEL CHICKEN",
            "Sesame Chicken": "SESAME CHICKEN",
            "Walnut Prawns": "WALNUT PRAWNS",
            "Honey Glazed Barbecued Pork": "HONEY GLAZED BARBECUED PORK",
            "Spring Egg Rolls": "SPRING EGG ROLLS (4)",
            "Golden Pot Stickers": "GOLDEN POT STICKERS (6)",
            "Chicken Salad": "CHICKEN SALAD",
            "Wonton Soup": "WONTON SOUP",
            "Hot & Sour Soup": "MIXED VEGETABLES SOUP",
            "Barbecued Pork Wonton Soup": "BARBECUED PORK WONTON SOUP",
            "Beef Wonton Soup": "BEEF WONTON SOUP",
            "Chicken Wonton Soup": "CHICKEN WONTON SOUP",
            "Roasted Duck Wonton Soup": "ROASTED DUCK WONTON SOUP",
            "Shrimp Wonton Soup": "SHRIMP WONTON SOUP",
            "Barbecued Pork Noodle Soup": "BARBECUED PORK NOODLE SOUP",
            "Beef Noodle Soup": "BEEF NOODLE SOUP",
            "Chicken Noodle Soup": "CHICKEN NOODLE SOUP",
            "Roasted Duck Noodle Soup": "ROASTED DUCK NOODLE SOUP",
            "Shrimp Noodle Soup": "SHRIMP NOODLE SOUP",
            "Eggplant with Chicken, Shrimp in Special Sauce": "EGGPLANT W/ CHICKEN, SHRIMP IN SPECIAL SAUCE",
            "Ginger Soy Chicken": "BEEF W/ GINGER & SCALLIONS ON RICE"
        }
        
        try:
            # Get sample values from DishType.json
            json_file = '/home/fizz/work/res-menu-store/auto/tmp/DishType.json'
            sample_values = self.extract_sample_values_from_json(json_file)
            
            mapping = {}
            for sample_value in sample_values:
                # Try to find exact mapping first
                if sample_value in SAMPLE_MAPPINGS:
                    menu_name = SAMPLE_MAPPINGS[sample_value]
                    if menu_name in MENU_PRICES:
                        price = MENU_PRICES[menu_name]
                        category = self._determine_category(menu_name)
                        mapping[sample_value] = {
                            'menu_name': menu_name,
                            'price': price,
                            'category': category
                        }
                        continue
                
                # Try to find by normalized matching
                sample_upper = sample_value.upper().replace('W/', 'WITH').replace('&', 'AND')
                found = False
                for menu_name, price in MENU_PRICES.items():
                    menu_normalized = menu_name.replace('W/', 'WITH').replace('&', 'AND')
                    if sample_upper == menu_normalized or sample_upper in menu_normalized:
                        category = self._determine_category(menu_name)
                        mapping[sample_value] = {
                            'menu_name': menu_name,
                            'price': price,
                            'category': category
                        }
                        found = True
                        break
                
                # If still not found, use sample name as menu name with default price
                if not found:
                    category = self._determine_category(sample_value)
                    mapping[sample_value] = {
                        'menu_name': sample_value,
                        'price': '12.00',  # Default price
                        'category': category
                    }
            
            logger.info(f"Created mapping for {len(mapping)} sample values")
            return mapping
            
        except Exception as e:
            logger.error(f"Error creating sample to menu mapping: {str(e)}")
            return {}
    
    def extract_sample_values_from_json(self, json_file_path: str) -> List[str]:
        """Extract sample values from DishType.json"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            sample_values = []
            for slot_type_value in data.get('slotTypeValues', []):
                sample_value = slot_type_value.get('sampleValue', {}).get('value')
                if sample_value:
                    sample_values.append(sample_value)
            
            return sample_values
        except Exception as e:
            logger.error(f"Error extracting sample values: {str(e)}")
            return []

    def load_menu_from_sample_mapping(self, json_file_path: str = None) -> bool:
        """
        Load menu items using sample names as primary keys
        
        Args:
            json_file_path: Path to DishType.json file
            
        Returns:
            bool: Success status
        """
        try:
            json_file = json_file_path or '/home/fizz/work/res-menu-store/auto/tmp/DishType.json'
            
            # Extract sample values with synonyms
            sample_data = self.extract_sample_values_with_synonyms(json_file)
            
            # Create mapping from sample names to menu items
            sample_to_menu = self.create_sample_to_menu_mapping()
            
            items_loaded = 0
            current_time = datetime.utcnow().isoformat()
            
            for sample_name, sample_info in sample_data.items():
                try:
                    # Get menu mapping for this sample
                    menu_mapping = sample_to_menu.get(sample_name, {})
                    
                    menu_name = menu_mapping.get('menu_name', sample_name)
                    price_str = menu_mapping.get('price', '0.00')
                    category = menu_mapping.get('category', 'MISCELLANEOUS')
                    
                    # Prepare item for DynamoDB
                    item = {
                        'sample_name': sample_name,  # Primary key
                        'menu_english_name': menu_name,
                        'menu_chinese_name': sample_info.get('chinese_synonym', ''),
                        'category': category,
                        'price': self.normalize_price(price_str),
                        'price_display': f"${price_str}",
                        'available': True,
                        'synonyms': sample_info.get('synonyms', []),
                        'created_at': current_time,
                        'updated_at': current_time
                    }
                    
                    # Save to DynamoDB
                    self.table.put_item(Item=item)
                    items_loaded += 1
                    
                    if items_loaded % 10 == 0:
                        logger.info(f"Loaded {items_loaded} items...")
                        
                except Exception as e:
                    logger.error(f"Error loading item {sample_name}: {str(e)}")
                    continue
            
            logger.info(f"Successfully loaded {items_loaded} menu items using sample names as keys")
            return True
            
        except Exception as e:
            logger.error(f"Error loading menu from sample mapping: {str(e)}")
            return False

    def normalize_price(self, price_str: str) -> Decimal:
        """Convert price string to Decimal for DynamoDB storage"""
        try:
            # Remove $ sign and extra text, convert to Decimal
            clean_price = price_str.replace('$', '').split()[0]
            return Decimal(clean_price)
        except:
            return Decimal('0.00')

    def _determine_category(self, item_name: str) -> str:
        """Determine category based on item name"""
        name_upper = item_name.upper()
        
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

    # ===== OPTIMIZED QUERY FUNCTIONS USING SAMPLE NAMES =====

    def get_item_by_sample_name(self, sample_name: str) -> Optional[Dict]:
        """
        Get menu item by sample name (PRIMARY KEY) - FASTEST LOOKUP
        
        Args:
            sample_name: Sample name from DishType.json (e.g., "Kung Pao Chicken")
            
        Returns:
            Dict or None: Menu item data
        """
        try:
            response = self.table.get_item(Key={'sample_name': sample_name})
            return response.get('Item')
            
        except Exception as e:
            logger.error(f"Error getting item by sample name {sample_name}: {str(e)}")
            return None

    def get_price_by_sample_name(self, sample_name: str) -> Optional[float]:
        """
        Get price by sample name - OPTIMIZED FOR LEX BOT
        
        Args:
            sample_name: Sample name from DishType.json
            
        Returns:
            float or None: Price value
        """
        try:
            item = self.get_item_by_sample_name(sample_name)
            return float(item['price']) if item else None
            
        except Exception as e:
            logger.error(f"Error getting price for {sample_name}: {str(e)}")
            return None

    def batch_get_prices(self, sample_names: List[str]) -> Dict[str, float]:
        """
        Get multiple prices in a single request - OPTIMIZED FOR ORDER PROCESSING
        
        Args:
            sample_names: List of sample names
            
        Returns:
            Dict: {sample_name: price}
        """
        try:
            # Prepare batch get request
            request_items = {
                self.table_name: {
                    'Keys': [{'sample_name': name} for name in sample_names]
                }
            }
            
            response = self.dynamodb.batch_get_item(RequestItems=request_items)
            
            prices = {}
            for item in response.get('Responses', {}).get(self.table_name, []):
                prices[item['sample_name']] = float(item['price'])
            
            return prices
            
        except Exception as e:
            logger.error(f"Error batch getting prices: {str(e)}")
            return {}

    def calculate_order_total_optimized(self, order_items: List[Dict]) -> Dict:
        """
        Calculate order total using optimized sample name lookups
        
        Args:
            order_items: List of order items with format:
                [
                    {"sample_name": "Kung Pao Chicken", "quantity": 2},
                    {"sample_name": "Beef with Broccoli", "quantity": 1}
                ]
                
        Returns:
            Dict: Order calculation results
        """
        try:
            # Extract all sample names for batch lookup
            sample_names = [item.get('sample_name', '') for item in order_items]
            
            # Get all prices in single batch request
            prices = self.batch_get_prices(sample_names)
            
            order_details = []
            subtotal = Decimal('0.00')
            items_not_found = []
            
            for order_item in order_items:
                sample_name = order_item.get('sample_name', '')
                quantity = int(order_item.get('quantity', 1))
                
                if sample_name in prices:
                    unit_price = Decimal(str(prices[sample_name]))
                    line_total = unit_price * quantity
                    
                    order_details.append({
                        'sample_name': sample_name,
                        'quantity': quantity,
                        'unit_price': float(unit_price),
                        'line_total': float(line_total)
                    })
                    
                    subtotal += line_total
                else:
                    items_not_found.append(sample_name)
            
            # Calculate tax (8.5% tax rate)
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
                'items_not_found': [item.get('sample_name', '') for item in order_items],
                'subtotal': 0.0,
                'tax_amount': 0.0,
                'total': 0.0
            }

    def update_price_by_sample_name(self, sample_name: str, new_price: str) -> bool:
        """
        Update price using sample name
        
        Args:
            sample_name: Sample name (primary key)
            new_price: New price as string
            
        Returns:
            bool: Success status
        """
        try:
            current_time = datetime.utcnow().isoformat()
            
            self.table.update_item(
                Key={'sample_name': sample_name},
                UpdateExpression='SET price = :price, price_display = :display, updated_at = :time',
                ExpressionAttributeValues={
                    ':price': self.normalize_price(new_price),
                    ':display': f"${new_price}",
                    ':time': current_time
                }
            )
            
            logger.info(f"Updated price for {sample_name} to ${new_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating price for {sample_name}: {str(e)}")
            return False

    def search_by_category(self, category: str) -> List[Dict]:
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

    def get_all_sample_names(self) -> List[str]:
        """Get all available sample names (for Lex bot slot values)"""
        try:
            response = self.table.scan(
                ProjectionExpression='sample_name'
            )
            
            return [item['sample_name'] for item in response.get('Items', [])]
            
        except Exception as e:
            logger.error(f"Error getting sample names: {str(e)}")
            return []

    def validate_sample_name(self, sample_name: str) -> bool:
        """Quickly validate if sample name exists"""
        return self.get_item_by_sample_name(sample_name) is not None


def main():
    """Demo the optimized manager"""
    # Initialize optimized manager
    manager = OptimizedMenuDynamoDBManager()
    
    print("=== Optimized DynamoDB Menu Manager (Sample Names as Keys) ===")
    
    # Create table (uncomment if table doesn't exist)
    # print("Creating optimized table...")
    # manager.create_table()
    
    # Load menu using sample names as keys
    print("Loading menu items using sample names as primary keys...")
    success = manager.load_menu_from_sample_mapping()
    
    if success:
        print("✅ Optimized menu loaded successfully!")
        
        # Demo: Fast price lookup by sample name
        print("\n=== Demo: Fast price lookup by sample name ===")
        sample_name = "Kung Pao Chicken"
        price = manager.get_price_by_sample_name(sample_name)
        print(f"{sample_name}: ${price}")
        
        # Demo: Batch price lookup
        print("\n=== Demo: Batch price lookup ===")
        sample_names = ["Kung Pao Chicken", "Beef with Broccoli", "Steamed Rice"]
        prices = manager.batch_get_prices(sample_names)
        for name, price in prices.items():
            print(f"{name}: ${price}")
        
        # Demo: Optimized order calculation
        print("\n=== Demo: Optimized order calculation ===")
        sample_order = [
            {"sample_name": "Kung Pao Chicken", "quantity": 2},
            {"sample_name": "Beef with Broccoli", "quantity": 1},
            {"sample_name": "Steamed Rice", "quantity": 2}
        ]
        
        order_result = manager.calculate_order_total_optimized(sample_order)
        print("Order Details:")
        for detail in order_result['order_details']:
            print(f"  {detail['quantity']}x {detail['sample_name']} @ ${detail['unit_price']} = ${detail['line_total']}")
        
        print(f"\nSubtotal: ${order_result['subtotal']:.2f}")
        print(f"Tax: ${order_result['tax_amount']:.2f}")
        print(f"Total: ${order_result['total']:.2f}")
        
        # Demo: Get all sample names (for Lex bot)
        print(f"\n=== Available Sample Names for Lex Bot ===")
        all_names = manager.get_all_sample_names()
        print(f"Total sample names: {len(all_names)}")
        print("First 10 sample names:")
        for name in all_names[:10]:
            print(f"- {name}")
            
    else:
        print("❌ Failed to load optimized menu items")


if __name__ == "__main__":
    main()