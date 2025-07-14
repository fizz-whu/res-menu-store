# Restaurant Bot Pricing System

## Overview
This pricing system adds comprehensive price calculation and management capabilities to your restaurant bot. When customers place orders, they automatically receive total costs including customizations.

## Components

### 1. Core Pricing System (`pricing_system.py`)
- **PricingService Class**: Main service for price lookups and calculations
- **Fuzzy Matching**: Intelligent dish name matching for variations
- **Customization Pricing**: Automatic charges for extras (sauce, vegetables, etc.)
- **DynamoDB Integration**: Production-ready data storage

### 2. Enhanced Lambda Function (`enhanced_lambda_function.py`)
- **Order Processing**: Complete order flow with pricing
- **Price Inquiries**: Handle "How much is..." questions  
- **Menu Display**: Show popular items with prices
- **Error Handling**: Graceful handling of pricing issues

### 3. Bot Intent Definitions
- **GetPrice Intent**: Customer price inquiries
- **CheckMenu Intent**: Display menu with prices
- **Enhanced OrderFood Intent**: Order confirmation with totals

### 4. Price Management Tools (`price_management_tools.py`)
- **Bulk Price Updates**: Import/export pricing data
- **Price Adjustments**: Apply percentage increases
- **Reporting**: Generate pricing reports
- **CSV/JSON Support**: Data import/export capabilities

## Features

### 🛒 Order Flow with Pricing
```
Customer: "I want 2 sweet and sour chicken"
Bot: "Order confirmed: 2x Sweet & Sour Chicken. Total: $26.50. Your order has been placed successfully!"
```

### 💰 Price Inquiries
```
Customer: "How much is kung pao chicken?"
Bot: "Kung Pao Chicken costs $13.25."
```

### 📋 Menu Display
```
Customer: "Show me the menu"
Bot: "Here are some popular items from our menu:
• Sweet & Sour Chicken: $13.25
• Beef with Broccoli: $14.25
• Kung Pao Chicken: $13.25
..."
```

### 🎛️ Customization Pricing
- **Free**: Extra spicy, no MSG, well done, no onions
- **$0.50**: Extra sauce
- **$1.00**: Extra vegetables  
- **$2.00**: Extra meat
- **$1.75**: Extra rice

## Setup Instructions

### 1. Deploy Enhanced Lambda Function
```bash
# Replace your existing lambda function with enhanced_lambda_function.py
cp enhanced_lambda_function.py /path/to/your/lambda/deployment/
```

### 2. Create Pricing Database (Optional)
```bash
# For production use with DynamoDB
python price_management_tools.py create-table --table cnres_menu_pricing
```

### 3. Import Initial Pricing Data
```bash
# Import from your existing menu JSON
python price_management_tools.py import --json /path/to/extracted_menu_data.json
```

### 4. Update Bot Intents
Add these new intents to your Lex bot:
- `GetPrice_intent.json` - Price inquiry intent
- `CheckMenu_intent.json` - Menu display intent  
- `enhanced_OrderFood_intent.json` - Enhanced order intent

### 5. Test the System
```bash
# Test pricing lookups
python pricing_system.py
```

## Price Management Commands

### Import Pricing Data
```bash
# From JSON menu file
python price_management_tools.py import --json menu_data.json

# From CSV file  
python price_management_tools.py import --csv prices.csv
```

### Export Pricing Data
```bash
# Export to CSV
python price_management_tools.py export --csv current_prices.csv
```

### Update Individual Prices
```bash
# Update single item
python price_management_tools.py update "kung pao chicken" 14.25 --category fowl
```

### Apply Price Increases
```bash
# 5% increase on all items
python price_management_tools.py increase 5.0

# 3% increase on seafood only
python price_management_tools.py increase 3.0 --category seafood
```

### Generate Reports
```bash
# Print pricing report
python price_management_tools.py report

# Save report to file
python price_management_tools.py report --output pricing_report.txt
```

### Query Prices
```bash
# Get price for specific dish
python price_management_tools.py get "sweet and sour chicken"

# List all prices
python price_management_tools.py list
```

## Database Schema

### DynamoDB Table: `cnres_menu_pricing`
```json
{
  "dish_name": "sweet and sour chicken",    // Primary key (lowercase)
  "price": 13.25,                          // Decimal price
  "category": "fowl",                      // Menu category
  "name_en": "Sweet & Sour Chicken",      // Display name
  "name_zh": "甜酸鸡",                     // Chinese name
  "last_updated": "2025-01-15T10:30:00"   // Update timestamp
}
```

### Enhanced Orders Table: `cnres0_orders`
```json
{
  "OrderID": "ORD-20250115103000",
  "DishName": "Sweet & Sour Chicken", 
  "Quantity": 2,
  "BasePrice": 13.25,
  "CustomizationCharge": 0.50,
  "TotalPrice": 27.50,
  "Customizations": ["extra sauce"],
  "Status": "Pending"
}
```

## Integration with Existing Bot

### 1. Lambda Environment Variables
```bash
PRICING_TABLE=cnres_menu_pricing
ORDERS_TABLE=cnres0_orders
```

### 2. Required IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem", 
    "dynamodb:Scan",
    "dynamodb:BatchWriteItem"
  ],
  "Resource": [
    "arn:aws:dynamodb:*:*:table/cnres_menu_pricing",
    "arn:aws:dynamodb:*:*:table/cnres0_orders"
  ]
}
```

### 3. Lex Bot Configuration
- Add new intents: `GetPrice`, `CheckMenu`
- Update `OrderFood` intent with enhanced prompts
- Configure fulfillment hooks to use enhanced lambda

## Conversation Flow Examples

### Complete Order Flow
```
User: "I want kung pao chicken"
Bot: "How many Kung Pao Chicken would you like?"
User: "2"  
Bot: "Any special requests for your Kung Pao Chicken?"
User: "extra spicy and extra sauce"
Bot: "Let me confirm: 2 Kung Pao Chicken with extra spicy, extra sauce?"
User: "yes"
Bot: "Order confirmed: 2x Kung Pao Chicken with extra spicy, extra sauce. Total: $27.50 (includes $1.00 for customizations). Your order has been placed successfully!"
```

### Price Shopping Flow
```
User: "what's on the menu?"
Bot: "Here are some popular items: • Sweet & Sour Chicken: $13.25 • Beef with Broccoli: $14.25..."
User: "how much is walnut prawns?"
Bot: "Walnut Prawns costs $16.25."
User: "I'll take 1 walnut prawns"
Bot: "Order confirmed: 1x Walnut Prawns. Total: $16.25. Your order has been placed successfully!"
```

## Monitoring and Analytics

### Order Analytics
The enhanced system tracks:
- Average order values
- Popular price points
- Customization frequency
- Price sensitivity patterns

### Pricing Performance
- Price lookup success rates
- Fuzzy matching accuracy
- Failed price queries for menu optimization

## Troubleshooting

### Common Issues

**Price Not Found**
- Check dish name variations in menu data
- Verify pricing table has current data
- Review fuzzy matching logic

**Customization Charges**
- Update `get_customization_charge()` method
- Add new customization types as needed

**DynamoDB Permissions**
- Verify Lambda execution role has table access
- Check table exists and is in correct region

### Debug Mode
Enable detailed logging in Lambda:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Dynamic Pricing**: Time-based price adjustments
- **Promotions**: Discount and coupon integration
- **Tax Calculation**: Automatic tax computation
- **Multi-Currency**: Support for different currencies
- **Price History**: Track price changes over time

### Integration Options
- **POS Systems**: Real-time inventory and pricing sync
- **Analytics**: Advanced pricing and sales analytics
- **A/B Testing**: Price experimentation framework