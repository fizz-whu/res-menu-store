#!/usr/bin/env python3
"""
Amazon Lex Bot Manager
A tool to download, edit, and upload Lex bot components (intents and slots)
Note: Lambda function management has been moved to lambda_function_manager.py
"""

import csv
import json
import os
import boto3
from typing import List, Dict, Any, Optional
import argparse
from pathlib import Path


class LexBotManager:
    def __init__(self, debug=False):
        self.download_dir = Path('./lex_downloads')
        self.download_dir.mkdir(exist_ok=True)
        self.clients = {}
        self.debug = debug
    
    def read_bot_ids_from_csv(self, csv_file: str = 'bot_ids.csv') -> List[Dict[str, str]]:
        """Read bot IDs from CSV file"""
        bots = []
        try:
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'bot_id' in row and 'region' in row:
                        bots.append(row)
                    else:
                        print(f"Warning: Missing 'bot_id' or 'region' column in row: {row}")
            return bots
        except FileNotFoundError:
            print(f"Error: CSV file '{csv_file}' not found")
            return []
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []
    
    def get_clients(self, region: str):
        """Get or create AWS clients for the specified region"""
        if region not in self.clients:
            self.clients[region] = {
                'lex': boto3.client('lexv2-models', region_name=region)
            }
        return self.clients[region]
    
    def _debug_print(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"DEBUG: {message}")
    
    def list_bot_components(self, bot_id: str, region: str) -> Dict[str, List[Dict[str, Any]]]:
        """List all components (intents, slots) of a bot"""
        components = {
            'intents': [],
            'slots': []
        }
        
        try:
            clients = self.get_clients(region)
            lex_client = clients['lex']
            
            # Get bot details first
            bot_response = lex_client.describe_bot(botId=bot_id)
            bot_name = bot_response['botName']
            
            # List bot versions to get the latest
            versions_response = lex_client.list_bot_versions(botId=bot_id)
            latest_version = versions_response['botVersionSummaries'][0]['botVersion']
            
            # List bot locales
            locales_response = lex_client.list_bot_locales(
                botId=bot_id,
                botVersion=latest_version
            )
            
            for locale in locales_response['botLocaleSummaries']:
                locale_id = locale['localeId']
                
                # List intents
                intents_response = lex_client.list_intents(
                    botId=bot_id,
                    botVersion=latest_version,
                    localeId=locale_id
                )
                
                for intent in intents_response['intentSummaries']:
                    components['intents'].append({
                        'name': intent['intentName'],
                        'id': intent['intentId'],
                        'locale': locale_id,
                        'bot_id': bot_id,
                        'bot_version': latest_version,
                        'region': region
                    })
                
                # List slot types
                slots_response = lex_client.list_slot_types(
                    botId=bot_id,
                    botVersion=latest_version,
                    localeId=locale_id
                )
                
                for slot in slots_response['slotTypeSummaries']:
                    components['slots'].append({
                        'name': slot['slotTypeName'],
                        'id': slot['slotTypeId'],
                        'locale': locale_id,
                        'bot_id': bot_id,
                        'bot_version': latest_version,
                        'region': region
                    })
            
        except Exception as e:
            print(f"Error listing bot components: {e}")
        
        return components
    
    
    
    def display_selection_menu(self, components: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """Display interactive menu for component selection"""
        all_items = []
        
        # Flatten all components into a single list
        for component_type, items in components.items():
            for item in items:
                item['type'] = component_type
                all_items.append(item)
        
        if not all_items:
            print("No components found for this bot.")
            return None
        
        print("\nAvailable Components:")
        print("-" * 50)
        
        for i, item in enumerate(all_items, 1):
            component_type = item['type']
            name = item['name']
            
            if component_type == 'lambda_functions':
                # Show Lambda function with usage information
                connection_type = item.get('connection_type', 'unknown')
                usage = item.get('usage', [])
                
                print(f"{i}. [{component_type.upper()}] {name} ({connection_type.upper()})")
                
                if usage:
                    print(f"    Used in:")
                    for use in usage:
                        intent_name = use['intent_name']
                        hook_type = use['hook_type']
                        description = use['description']
                        locale_info = use['locale']
                        print(f"      - Intent: {intent_name} ({hook_type}) - {description} [Locale: {locale_info}]")
                else:
                    if connection_type == 'direct':
                        print(f"    Usage: Connected to bot but no specific intent usage found")
                    elif connection_type == 'inferred':
                        print(f"    Usage: Potentially related (name/description match)")
                    elif connection_type == 'debug':
                        print(f"    Usage: Debug mode - verify connection manually")
                    else:
                        print(f"    Usage: Unknown connection")
            else:
                locale = item.get('locale', 'N/A')
                print(f"{i}. [{component_type.upper()}] {name} (Locale: {locale})")
        
        print(f"{len(all_items) + 1}. Exit")
        
        try:
            choice = int(input("\nSelect a component to download (enter number): "))
            if 1 <= choice <= len(all_items):
                return all_items[choice - 1]
            elif choice == len(all_items) + 1:
                return None
            else:
                print("Invalid selection.")
                return None
        except ValueError:
            print("Please enter a valid number.")
            return None
    
    def download_component(self, component: Dict[str, Any]) -> Optional[str]:
        """Download selected component to local file"""
        component_type = component['type']
        name = component['name']
        region = component['region']
        
        # Create directory structure
        bot_dir = self.download_dir / component['bot_id']
        type_dir = bot_dir / component_type
        type_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = type_dir / f"{name}.json"
        
        try:
            clients = self.get_clients(region)
            lex_client = clients['lex']
            
            if component_type == 'intents':
                response = lex_client.describe_intent(
                    botId=component['bot_id'],
                    botVersion=component['bot_version'],
                    localeId=component['locale'],
                    intentId=component['id']
                )
                # Remove metadata that shouldn't be edited
                content = self._clean_intent_response(response)
                
            elif component_type == 'slots':
                response = lex_client.describe_slot_type(
                    botId=component['bot_id'],
                    botVersion=component['bot_version'],
                    localeId=component['locale'],
                    slotTypeId=component['id']
                )
                content = self._clean_slot_response(response)
                
            else:
                print(f"Unknown component type: {component_type}")
                return None
            
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2, default=str)
            
            print(f"Downloaded {component_type}: {name} to {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"Error downloading component: {e}")
            return None
    
    def _clean_intent_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Clean intent response for editing"""
        keys_to_keep = [
            'intentName', 'description', 'sampleUtterances', 'slotPriorities',
            'fulfillmentCodeHook', 'confirmationSetting', 'promptSpecification',
            'declinationResponse', 'inputContexts', 'outputContexts'
        ]
        return {k: v for k, v in response.items() if k in keys_to_keep}
    
    def _clean_slot_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Clean slot response for editing"""
        keys_to_keep = [
            'slotTypeName', 'description', 'slotTypeValues', 'valueSelectionStrategy',
            'parentSlotTypeSignature', 'externalSourceSetting'
        ]
        return {k: v for k, v in response.items() if k in keys_to_keep}
    
    def upload_component(self, file_path: str, region: str = None) -> bool:
        """Upload modified component back to Lex"""
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)
            
            # Determine component type from file path
            path_parts = Path(file_path).parts
            component_type = path_parts[-2]  # Parent directory name
            bot_id = path_parts[-3]  # Grandparent directory name
            
            # If region not provided, try to determine from content or use default
            if not region:
                region = content.get('region', 'us-east-1')
            
            if component_type == 'intents':
                return self._upload_intent(content, bot_id, file_path, region)
            elif component_type == 'slots':
                return self._upload_slot(content, bot_id, file_path, region)
            else:
                print(f"Unknown component type: {component_type}")
                return False
            
        except Exception as e:
            print(f"Error uploading component: {e}")
            return False
    
    def _upload_intent(self, content: Dict[str, Any], bot_id: str, file_path: str, region: str) -> bool:
        """Upload intent to Lex"""
        try:
            clients = self.get_clients(region)
            lex_client = clients['lex']
            
            # You'll need to get the correct bot version and locale
            # This is simplified - in practice, store this info with the downloaded file
            intent_name = content['intentName']
            
            response = lex_client.update_intent(
                botId=bot_id,
                botVersion='DRAFT',
                localeId='en_US',  # This should be stored/retrieved properly
                intentId=intent_name,  # This should be the actual intent ID
                **content
            )
            print(f"Successfully uploaded intent: {intent_name}")
            return True
        except Exception as e:
            print(f"Error uploading intent: {e}")
            return False
    
    def _upload_slot(self, content: Dict[str, Any], bot_id: str, file_path: str, region: str) -> bool:
        """Upload slot to Lex"""
        try:
            clients = self.get_clients(region)
            lex_client = clients['lex']
            
            slot_name = content['slotTypeName']
            
            response = lex_client.update_slot_type(
                botId=bot_id,
                botVersion='DRAFT',
                localeId='en_US',  # This should be stored/retrieved properly
                slotTypeId=slot_name,  # This should be the actual slot ID
                **content
            )
            print(f"Successfully uploaded slot: {slot_name}")
            return True
        except Exception as e:
            print(f"Error uploading slot: {e}")
            return False
    


def main():
    parser = argparse.ArgumentParser(description='Amazon Lex Bot Manager - Manages Lex intents and slots')
    parser.add_argument('--csv', default='bot_ids.csv', help='CSV file containing bot IDs (default: bot_ids.csv)')
    parser.add_argument('--upload', help='Upload a modified component file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--lambda', action='store_true', help='Also manage Lambda functions (uses lambda_function_manager)')
    
    args = parser.parse_args()
    
    manager = LexBotManager(debug=args.debug)
    
    # Import Lambda manager if requested
    lambda_manager = None
    if args.lambda_:
        try:
            from lambda_function_manager import LambdaFunctionManager
            lambda_manager = LambdaFunctionManager(debug=args.debug)
        except ImportError:
            print("Warning: lambda_function_manager.py not found. Lambda functions will not be managed.")
    
    if args.upload:
        # Upload mode
        success = manager.upload_component(args.upload)
        if success:
            print("Upload completed successfully!")
        else:
            print("Upload failed!")
        return
    
    # Download mode
    bots = manager.read_bot_ids_from_csv(args.csv)
    
    if not bots:
        print("No bots found in CSV file.")
        return
    
    print("Available bots:")
    for i, bot in enumerate(bots, 1):
        bot_id = bot['bot_id']
        bot_name = bot.get('bot_name', 'Unknown')
        region = bot.get('region', 'us-east-1')
        print(f"{i}. {bot_name} ({bot_id}) - Region: {region}")
    
    try:
        choice = int(input("\nSelect a bot (enter number): "))
        if 1 <= choice <= len(bots):
            selected_bot = bots[choice - 1]
            bot_id = selected_bot['bot_id']
            region = selected_bot.get('region', 'us-east-1')
            
            print(f"\nFetching components for bot: {bot_id} in region: {region}")
            components = manager.list_bot_components(bot_id, region)
            
            # Add Lambda functions if Lambda manager is available
            if lambda_manager:
                lex_client = manager.get_clients(region)['lex']
                lambda_functions = lambda_manager.find_lambda_functions_for_bot(
                    lex_client, bot_id, region, 
                    include_fallback=False, 
                    export_bot=False
                )
                components['lambda_functions'] = lambda_functions
                
                # Show Lambda usage summary if any Lambda functions were found
                if lambda_functions:
                    lambda_manager.display_lambda_usage_summary(lambda_functions)
            
            while True:
                selected_component = manager.display_selection_menu(components)
                if selected_component is None:
                    break
                
                # Handle Lambda function downloads differently
                if selected_component.get('type') == 'lambda_functions' and lambda_manager:
                    selected_component['bot_id'] = bot_id  # Add bot_id for download directory
                    file_path = lambda_manager.download_lambda_function(selected_component)
                else:
                    file_path = manager.download_component(selected_component)
                
                if file_path:
                    print(f"\nComponent downloaded to: {file_path}")
                    print("You can now edit the file and use --upload to update the bot.")
        else:
            print("Invalid selection.")
    
    except ValueError:
        print("Please enter a valid number.")
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()