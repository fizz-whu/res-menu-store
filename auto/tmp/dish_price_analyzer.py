import json
import csv
from typing import List, Dict, Tuple

# Hard-coded menu prices - complete list from menu.csv
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
    "DRINKS": "1.85",
    "Ginger Soy Chicken": "NOT FOUND"
}

def get_price_from_hardcoded(dish_name: str) -> str:
    """Get price from hard-coded menu prices dictionary"""
    # Try exact match first
    if dish_name in MENU_PRICES:
        return MENU_PRICES[dish_name]
    
    # Try case-insensitive match
    dish_upper = dish_name.upper()
    for menu_item, price in MENU_PRICES.items():
        if menu_item.upper() == dish_upper:
            return price
    
    # Try partial match
    for menu_item, price in MENU_PRICES.items():
        if dish_upper in menu_item.upper() or menu_item.upper() in dish_upper:
            return price
    
    return "NOT FOUND"

def get_requested_items_prices() -> Dict[str, str]:
    """Get prices for the specifically requested items"""
    requested_items = [
        "Ginger Soy Chicken",
        "Eggplant with Chicken, Shrimp in Special Sauce", 
        "Barbecued Pork Wonton Soup",
        "Beef Wonton Soup",
        "Chicken Wonton Soup", 
        "Roasted Duck Wonton Soup",
        "Shrimp Wonton Soup",
        "Barbecued Pork Noodle Soup",
        "Beef Noodle Soup",
        "Chicken Noodle Soup",
        "Roasted Duck Noodle Soup", 
        "Shrimp Noodle Soup"
    ]
    
    prices = {}
    for item in requested_items:
        price = get_price_from_hardcoded(item)
        prices[item] = price
    
    return prices

def extract_sample_values(json_file_path: str) -> List[str]:
    """Extract all sampleValue fields from DishType.json"""
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    sample_values = []
    for slot_type_value in data.get('slotTypeValues', []):
        sample_value = slot_type_value.get('sampleValue', {}).get('value')
        if sample_value:
            sample_values.append(sample_value)
    
    return sample_values

def find_prices_in_menu(csv_file_path: str, sample_values: List[str]) -> List[Tuple[str, str, str]]:
    """Find sample values in menu.csv and return their prices"""
    found_items = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            english_name = row['Item English Name'].strip()
            chinese_name = row['Item Chinese Name'].strip()
            price = row['Price'].strip()
            
            # Convert W/ to WITH in menu name for better matching
            normalized_menu_name = english_name.replace('W/', 'WITH').lower()
            
            # Check if any sample value matches the English name (case insensitive)
            for sample_value in sample_values:
                normalized_sample_value = sample_value.lower()
                if normalized_sample_value == english_name.lower() or normalized_sample_value == normalized_menu_name:
                    found_items.append((sample_value, english_name, price))
                    break
    
    return found_items

def analyze_dish_prices():
    """Main function to analyze dish prices"""
    print("=== HARD-CODED PRICE LOOKUP DEMONSTRATION ===")
    
    # Get prices for specifically requested items
    requested_prices = get_requested_items_prices()
    print("\nPrices for specifically requested items:")
    print("-" * 60)
    for item, price in requested_prices.items():
        print(f"{item}: ${price}")
    print("-" * 60)
    
    print(f"\nTotal items in hard-coded menu: {len(MENU_PRICES)}")
    
    # Also demonstrate the original CSV-based lookup
    print("\n=== ORIGINAL CSV-BASED ANALYSIS ===")
    json_file = '/home/fizz/work/res-menu-store/auto/tmp/DishType.json'
    csv_file = '/home/fizz/work/res-menu-store/auto/tmp/menu.csv'
    
    # Extract sample values from JSON
    print("Extracting sample values from DishType.json...")
    sample_values = extract_sample_values(json_file)
    print(f"Found {len(sample_values)} sample values")
    
    # Find prices in menu
    print("\nSearching for sample values in menu.csv...")
    found_items = find_prices_in_menu(csv_file, sample_values)
    
    print(f"\nFound {len(found_items)} matching items with prices:")
    print("-" * 60)
    for sample_value, menu_name, price in found_items:
        print(f"Sample Value: {sample_value}")
        print(f"Menu Name: {menu_name}")
        print(f"Price: {price}")
        print("-" * 60)
    
    # Show sample values that weren't found
    found_sample_values = {item[0] for item in found_items}
    not_found = [sv for sv in sample_values if sv not in found_sample_values]
    
    if not_found:
        print(f"\nSample values not found in menu ({len(not_found)}):")
        for item in not_found:  # Show all items
            print(f"- {item}")

if __name__ == "__main__":
    analyze_dish_prices()