#!/usr/bin/env python3
"""
Price Management Tools for Restaurant Bot
Tools for updating prices, managing menu items, and maintaining pricing data
"""

import json
import boto3
import csv
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class PriceManager:
    """Tool for managing restaurant pricing data"""
    
    def __init__(self, dynamodb_table: str = "cnres_menu_pricing"):
        self.dynamodb_table = dynamodb_table
        self.dynamodb = boto3.resource('dynamodb')
        self.table = None
        
        try:
            self.table = self.dynamodb.Table(self.dynamodb_table)
            self.table.load()
            print(f"✅ Connected to pricing table: {self.dynamodb_table}")
        except Exception as e:
            print(f"⚠️  Could not connect to pricing table: {e}")
    
    def create_pricing_table(self):
        """Create DynamoDB table for pricing data"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.dynamodb_table,
                KeySchema=[
                    {
                        'AttributeName': 'dish_name',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'dish_name',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            table.wait_until_exists()
            self.table = table
            print(f"✅ Created pricing table: {self.dynamodb_table}")
            
        except Exception as e:
            print(f"❌ Error creating table: {e}")
    
    def update_price(self, dish_name: str, new_price: float, category: str = None):
        """Update price for a single dish"""
        if not self.table:
            print("❌ No table connection")
            return False
        
        try:
            item = {
                'dish_name': dish_name.lower(),
                'price': Decimal(str(new_price)),
                'last_updated': datetime.now().isoformat()
            }
            
            if category:
                item['category'] = category
            
            self.table.put_item(Item=item)
            print(f"✅ Updated {dish_name}: ${new_price:.2f}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating {dish_name}: {e}")
            return False
    
    def bulk_update_prices(self, price_updates: List[Dict]):
        """Update multiple prices at once"""
        if not self.table:
            print("❌ No table connection")
            return
        
        success_count = 0
        error_count = 0
        
        with self.table.batch_writer() as batch:
            for update in price_updates:
                try:
                    item = {
                        'dish_name': update['dish_name'].lower(),
                        'price': Decimal(str(update['price'])),
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Add optional fields
                    for field in ['category', 'name_en', 'name_zh', 'description']:
                        if field in update:
                            item[field] = update[field]
                    
                    batch.put_item(Item=item)
                    success_count += 1
                    
                except Exception as e:
                    print(f"❌ Error updating {update.get('dish_name', 'unknown')}: {e}")
                    error_count += 1
        
        print(f"✅ Bulk update complete: {success_count} success, {error_count} errors")
    
    def import_from_json(self, json_file_path: str):
        """Import pricing data from menu JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
            
            price_updates = []
            
            # Process menu sections
            menu_sections = menu_data.get('menu_sections', {})
            
            for section_name, section_data in menu_sections.items():
                if isinstance(section_data, list):
                    # Standard menu section
                    for item in section_data:
                        if isinstance(item, dict) and 'price' in item:
                            # Handle different price formats
                            price_value = item['price']
                            if isinstance(price_value, str):
                                # Extract first number from string
                                import re
                                match = re.search(r'(\d+\.?\d*)', price_value)
                                if match:
                                    price_value = float(match.group(1))
                                else:
                                    continue
                            
                            update = {
                                'dish_name': item.get('name_en', '').lower(),
                                'price': float(price_value),
                                'category': section_name,
                                'name_en': item.get('name_en', ''),
                                'name_zh': item.get('name_zh', ''),
                                'full_price_info': str(item.get('price', ''))
                            }
                            price_updates.append(update)
            
            print(f"📋 Found {len(price_updates)} items to import")
            self.bulk_update_prices(price_updates)
            
        except Exception as e:
            print(f"❌ Error importing from JSON: {e}")
    
    def export_to_csv(self, output_file: str):
        """Export pricing data to CSV file"""
        if not self.table:
            print("❌ No table connection")
            return
        
        try:
            response = self.table.scan()
            items = response['Items']
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])
            
            # Write to CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                if items:
                    fieldnames = ['dish_name', 'price', 'category', 'name_en', 'name_zh', 'last_updated']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for item in items:
                        row = {}
                        for field in fieldnames:
                            value = item.get(field, '')
                            if isinstance(value, Decimal):
                                value = float(value)
                            row[field] = value
                        writer.writerow(row)
            
            print(f"✅ Exported {len(items)} items to {output_file}")
            
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")
    
    def import_from_csv(self, csv_file_path: str):
        """Import pricing data from CSV file"""
        try:
            price_updates = []
            
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    if row.get('dish_name') and row.get('price'):
                        try:
                            update = {
                                'dish_name': row['dish_name'].lower(),
                                'price': float(row['price']),
                                'category': row.get('category', ''),
                                'name_en': row.get('name_en', ''),
                                'name_zh': row.get('name_zh', '')
                            }
                            price_updates.append(update)
                        except ValueError:
                            print(f"⚠️  Skipping invalid price for {row.get('dish_name')}")
            
            print(f"📋 Found {len(price_updates)} items to import from CSV")
            self.bulk_update_prices(price_updates)
            
        except Exception as e:
            print(f"❌ Error importing from CSV: {e}")
    
    def get_price(self, dish_name: str) -> Optional[Dict]:
        """Get price information for a dish"""
        if not self.table:
            print("❌ No table connection")
            return None
        
        try:
            response = self.table.get_item(
                Key={'dish_name': dish_name.lower()}
            )
            
            if 'Item' in response:
                item = response['Item']
                return {
                    'dish_name': item.get('dish_name'),
                    'price': float(item.get('price', 0)),
                    'category': item.get('category', ''),
                    'name_en': item.get('name_en', ''),
                    'name_zh': item.get('name_zh', ''),
                    'last_updated': item.get('last_updated', '')
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting price for {dish_name}: {e}")
            return None
    
    def list_all_prices(self) -> List[Dict]:
        """Get all pricing data"""
        if not self.table:
            print("❌ No table connection")
            return []
        
        try:
            response = self.table.scan()
            items = response['Items']
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])
            
            # Convert to regular dicts
            result = []
            for item in items:
                price_info = {
                    'dish_name': item.get('dish_name'),
                    'price': float(item.get('price', 0)),
                    'category': item.get('category', ''),
                    'name_en': item.get('name_en', ''),
                    'name_zh': item.get('name_zh', ''),
                    'last_updated': item.get('last_updated', '')
                }
                result.append(price_info)
            
            return sorted(result, key=lambda x: x['category'])
            
        except Exception as e:
            print(f"❌ Error listing prices: {e}")
            return []
    
    def price_increase(self, percentage: float, category_filter: str = None):
        """Apply percentage price increase to all or filtered items"""
        if not self.table:
            print("❌ No table connection")
            return
        
        try:
            all_items = self.list_all_prices()
            
            if category_filter:
                items_to_update = [item for item in all_items if item['category'] == category_filter]
                print(f"📋 Applying {percentage}% increase to {len(items_to_update)} items in '{category_filter}' category")
            else:
                items_to_update = all_items
                print(f"📋 Applying {percentage}% increase to all {len(items_to_update)} items")
            
            price_updates = []
            for item in items_to_update:
                new_price = item['price'] * (1 + percentage / 100)
                # Round to nearest quarter
                new_price = round(new_price * 4) / 4
                
                update = {
                    'dish_name': item['dish_name'],
                    'price': new_price,
                    'category': item['category'],
                    'name_en': item['name_en'],
                    'name_zh': item['name_zh']
                }
                price_updates.append(update)
                
                print(f"  {item['name_en']}: ${item['price']:.2f} → ${new_price:.2f}")
            
            if input(f"\\nApply these price changes? (y/N): ").lower() == 'y':
                self.bulk_update_prices(price_updates)
            else:
                print("❌ Price increase cancelled")
                
        except Exception as e:
            print(f"❌ Error applying price increase: {e}")
    
    def generate_price_report(self, output_file: str = None):
        """Generate pricing report"""
        all_items = self.list_all_prices()
        
        if not all_items:
            print("❌ No pricing data found")
            return
        
        # Group by category
        categories = {}
        for item in all_items:
            category = item['category'] or 'Other'
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        report = []
        report.append("🍽️  Restaurant Pricing Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Items: {len(all_items)}")
        report.append("")
        
        total_value = 0
        for category, items in sorted(categories.items()):
            report.append(f"📋 {category.title()} ({len(items)} items)")
            report.append("-" * 30)
            
            category_value = 0
            for item in sorted(items, key=lambda x: x['price']):
                price = item['price']
                name = item['name_en'] or item['dish_name']
                report.append(f"  {name:<35} ${price:>6.2f}")
                category_value += price
                total_value += price
            
            avg_price = category_value / len(items) if items else 0
            report.append(f"  Category Average: ${avg_price:.2f}")
            report.append("")
        
        overall_avg = total_value / len(all_items) if all_items else 0
        report.append(f"📊 Overall Statistics:")
        report.append(f"  Total Categories: {len(categories)}")
        report.append(f"  Average Price: ${overall_avg:.2f}")
        report.append(f"  Price Range: ${min(item['price'] for item in all_items):.2f} - ${max(item['price'] for item in all_items):.2f}")
        
        report_text = "\\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"✅ Report saved to {output_file}")
        else:
            print(report_text)


def main():
    """Command line interface for price management"""
    parser = argparse.ArgumentParser(description='Restaurant Price Management Tool')
    parser.add_argument('--table', default='cnres_menu_pricing', help='DynamoDB table name')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create table
    subparsers.add_parser('create-table', help='Create pricing table')
    
    # Import data
    import_parser = subparsers.add_parser('import', help='Import pricing data')
    import_parser.add_argument('--json', help='Import from JSON file')
    import_parser.add_argument('--csv', help='Import from CSV file')
    
    # Export data
    export_parser = subparsers.add_parser('export', help='Export pricing data')
    export_parser.add_argument('--csv', required=True, help='Export to CSV file')
    
    # Update price
    update_parser = subparsers.add_parser('update', help='Update single item price')
    update_parser.add_argument('dish_name', help='Dish name')
    update_parser.add_argument('price', type=float, help='New price')
    update_parser.add_argument('--category', help='Category')
    
    # Price increase
    increase_parser = subparsers.add_parser('increase', help='Apply percentage price increase')
    increase_parser.add_argument('percentage', type=float, help='Percentage increase')
    increase_parser.add_argument('--category', help='Apply to specific category only')
    
    # Get price
    get_parser = subparsers.add_parser('get', help='Get price for dish')
    get_parser.add_argument('dish_name', help='Dish name')
    
    # List all
    subparsers.add_parser('list', help='List all prices')
    
    # Generate report
    report_parser = subparsers.add_parser('report', help='Generate pricing report')
    report_parser.add_argument('--output', help='Output file for report')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize price manager
    pm = PriceManager(args.table)
    
    if args.command == 'create-table':
        pm.create_pricing_table()
    
    elif args.command == 'import':
        if args.json:
            pm.import_from_json(args.json)
        elif args.csv:
            pm.import_from_csv(args.csv)
        else:
            print("❌ Specify --json or --csv file")
    
    elif args.command == 'export':
        pm.export_to_csv(args.csv)
    
    elif args.command == 'update':
        pm.update_price(args.dish_name, args.price, args.category)
    
    elif args.command == 'increase':
        pm.price_increase(args.percentage, args.category)
    
    elif args.command == 'get':
        price_info = pm.get_price(args.dish_name)
        if price_info:
            print(f"✅ {price_info['name_en']}: ${price_info['price']:.2f}")
            print(f"   Category: {price_info['category']}")
            print(f"   Last Updated: {price_info['last_updated']}")
        else:
            print(f"❌ Price not found for '{args.dish_name}'")
    
    elif args.command == 'list':
        prices = pm.list_all_prices()
        for item in prices:
            print(f"{item['name_en']:<35} ${item['price']:>6.2f} [{item['category']}]")
    
    elif args.command == 'report':
        pm.generate_price_report(args.output)


if __name__ == "__main__":
    main()