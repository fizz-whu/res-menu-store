#!/usr/bin/env python3
"""
Production script to create and populate DynamoDB table for restaurant menu
Uses sample names as primary keys for optimized Lex bot integration
"""

import boto3
import json
from decimal import Decimal
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MenuTableCreator:
    def __init__(self, table_name: str = "RestaurantMenuOptimized", region_name: str = "us-west-2"):
        self.table_name = table_name
        self.region_name = region_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        
    def create_table(self):
        """Create the optimized DynamoDB table"""
        try:
            logger.info(f"Creating table {self.table_name}...")
            
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'sample_name',
                        'KeyType': 'HASH'  # Primary key
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
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            logger.info("Waiting for table to be created...")
            table.wait_until_exists()
            logger.info("✅ Table created successfully!")
            return True
            
        except Exception as e:
            if 'ResourceInUseException' in str(e):
                logger.info("Table already exists, skipping creation...")
                return True
            else:
                logger.error(f"Error creating table: {str(e)}")
                return False

    def extract_sample_data(self, json_file_path: str):
        """Extract sample values and synonyms from DishType.json"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            sample_data = {}
            for slot_type_value in data.get('slotTypeValues', []):
                sample_value = slot_type_value.get('sampleValue', {}).get('value')
                if sample_value:
                    synonyms = []
                    chinese_synonym = ""
                    
                    for synonym in slot_type_value.get('synonyms', []):
                        synonym_value = synonym.get('value', '')
                        if synonym_value:
                            synonyms.append(synonym_value)
                            if any('\u4e00' <= char <= '\u9fff' for char in synonym_value):
                                chinese_synonym = synonym_value
                    
                    sample_data[sample_value] = {
                        'synonyms': synonyms,
                        'chinese_synonym': chinese_synonym
                    }
            
            logger.info(f"Extracted {len(sample_data)} sample values with synonyms")
            return sample_data
            
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            return {}

    def create_price_mappings(self):
        """Create mappings from sample names to menu items with prices"""
        
        # Complete menu prices from our analysis
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
        
        # Enhanced sample mappings based on our analysis
        SAMPLE_MAPPINGS = {
            # Exact matches from our successful mappings
            "Kung Pao Chicken": "KUNG PAO CHICKEN",
            "Beef with Broccoli": "BEEF W/ BROCCOLI", 
            "Sweet & Sour Chicken": "SWEET & SOUR CHICKEN",
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
            
            # Your requested items
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
            "Ginger Soy Chicken": "BEEF W/ GINGER & SCALLIONS ON RICE",
            
            # Additional common mappings
            "Fried Rice": "HOUSE SPECIAL FRIED RICE",
            "Shrimp Fried Rice": "SHRIMP FRIED RICE",
            "Chicken Fried Rice": "CHICKEN FRIED RICE",
            "Beef Fried Rice": "BEEF FRIED RICE",
            "House Special Fried Rice": "HOUSE SPECIAL FRIED RICE",
            "Yang Chow Fried Rice": "YANG CHOW FRIED RICE",
            "Curry Chicken": "CURRY CHICKEN",
            "Curry Beef": "CURRY BEEF",
            "Lemon Chicken": "LEMON CHICKEN",
            "Rainbow Chicken": "RAINBOW CHICKEN",
            "Orange Peel Beef": "ORANGE PEEL BEEF",
            "Mixed Vegetable Soup": "MIXED VEGETABLES SOUP",
            "Hot & Sour Soup": "MIXED VEGETABLES SOUP",
            "Seafood Bean Cake Soup": "SEAFOOD W/ BEAN CAKE SOUP",
            "Wor Wonton Soup": "WOR WONTON SOUP",
            "Chicken with Corn Soup": "CHICKEN W/ CORN SOUP",
            "Cashew Almond Chicken": "ALMOND CHICKEN",
            "House Special Chow Mein": "HOUSE SPECIAL CHOW MEIN",
            "Chicken Chow Mein": "CHICKEN CHOW MEIN",
            "Shrimp Chow Mein": "SHRIMP CHOW MEIN",
            "Hong Kong Style Family Dinner": "HONG KONG STYLE (MINIMUM FOR 2 PERSON)",
            "Peking Style Family Dinner": "PEKING STYLE (MINIMUM FOR 2 PERSON)"
        }
        
        return MENU_PRICES, SAMPLE_MAPPINGS

    def determine_category(self, item_name: str) -> str:
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

    def normalize_price(self, price_str: str) -> Decimal:
        """Convert price string to Decimal"""
        try:
            clean_price = price_str.replace('$', '').split()[0]
            return Decimal(clean_price)
        except:
            return Decimal('12.00')

    def populate_table(self, json_file_path: str = '/home/fizz/work/res-menu-store/auto/tmp/DishType.json'):
        """Populate the table with menu data"""
        try:
            table = self.dynamodb.Table(self.table_name)
            
            # Get sample data and price mappings
            sample_data = self.extract_sample_data(json_file_path)
            menu_prices, sample_mappings = self.create_price_mappings()
            
            logger.info(f"Populating table with {len(sample_data)} items...")
            
            items_loaded = 0
            current_time = datetime.utcnow().isoformat()
            
            for sample_name, sample_info in sample_data.items():
                try:
                    # Try to find price mapping
                    if sample_name in sample_mappings:
                        menu_name = sample_mappings[sample_name]
                        price = menu_prices.get(menu_name, '12.00')
                    else:
                        # Try fuzzy matching
                        menu_name = sample_name
                        price = '12.00'
                        
                        # Try normalized matching
                        sample_upper = sample_name.upper().replace('W/', 'WITH').replace('&', 'AND')
                        for menu_item, menu_price in menu_prices.items():
                            menu_normalized = menu_item.replace('W/', 'WITH').replace('&', 'AND')
                            if sample_upper == menu_normalized or sample_upper in menu_normalized or menu_normalized in sample_upper:
                                menu_name = menu_item
                                price = menu_price
                                break
                    
                    category = self.determine_category(menu_name)
                    
                    # Prepare DynamoDB item
                    item = {
                        'sample_name': sample_name,  # Primary key
                        'menu_english_name': menu_name,
                        'menu_chinese_name': sample_info.get('chinese_synonym', ''),
                        'category': category,
                        'price': self.normalize_price(price),
                        'price_display': f"${price}",
                        'available': True,
                        'synonyms': sample_info.get('synonyms', []),
                        'created_at': current_time,
                        'updated_at': current_time
                    }
                    
                    # Insert into DynamoDB
                    table.put_item(Item=item)
                    items_loaded += 1
                    
                    if items_loaded % 20 == 0:
                        logger.info(f"Loaded {items_loaded} items...")
                        
                except Exception as e:
                    logger.error(f"Error loading item {sample_name}: {str(e)}")
                    continue
            
            logger.info(f"✅ Successfully loaded {items_loaded} menu items!")
            return True
            
        except Exception as e:
            logger.error(f"Error populating table: {str(e)}")
            return False

    def test_table(self):
        """Test the populated table with sample queries"""
        try:
            table = self.dynamodb.Table(self.table_name)
            
            logger.info("Testing table with sample queries...")
            
            # Test 1: Get item by sample name
            test_items = ["Kung Pao Chicken", "Beef with Broccoli", "Steamed Rice"]
            
            for item_name in test_items:
                response = table.get_item(Key={'sample_name': item_name})
                if 'Item' in response:
                    item = response['Item']
                    logger.info(f"✅ {item_name}: ${item['price']} ({item['category']})")
                else:
                    logger.warning(f"⚠️  {item_name}: Not found")
            
            # Test 2: Count items by category
            logger.info("Counting items by category...")
            response = table.scan(ProjectionExpression='category')
            categories = {}
            for item in response.get('Items', []):
                cat = item['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            for category, count in sorted(categories.items()):
                logger.info(f"  {category}: {count} items")
            
            logger.info(f"✅ Total items in table: {sum(categories.values())}")
            return True
            
        except Exception as e:
            logger.error(f"Error testing table: {str(e)}")
            return False


def main():
    """Main function to create and populate the table"""
    logger.info("🚀 Creating and populating DynamoDB table for restaurant menu")
    logger.info("=" * 70)
    
    # Initialize creator
    creator = MenuTableCreator()
    
    try:
        # Step 1: Create table
        if creator.create_table():
            logger.info("✅ Table creation completed")
        else:
            logger.error("❌ Table creation failed")
            return
        
        # Step 2: Populate table
        if creator.populate_table():
            logger.info("✅ Table population completed")
        else:
            logger.error("❌ Table population failed")
            return
        
        # Step 3: Test table
        if creator.test_table():
            logger.info("✅ Table testing completed")
        else:
            logger.error("❌ Table testing failed")
            return
        
        logger.info("=" * 70)
        logger.info("🎉 DynamoDB table setup completed successfully!")
        logger.info(f"📋 Table name: {creator.table_name}")
        logger.info(f"🌍 Region: {creator.region_name}")
        logger.info("🤖 Ready for Lex bot integration!")
        
    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()