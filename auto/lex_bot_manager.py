#!/usr/bin/env python3
"""
Amazon Lex Bot Manager
A tool to download, edit, and upload Lex bot components (intents, slots, lambda functions)
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
                'lex': boto3.client('lexv2-models', region_name=region),
                'lambda': boto3.client('lambda', region_name=region)
            }
        return self.clients[region]
    
    def _debug_print(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"DEBUG: {message}")
    
    def list_bot_components(self, bot_id: str, region: str, include_fallback: bool = False, export_bot: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """List all components (intents, slots) of a bot"""
        components = {
            'intents': [],
            'slots': [],
            'lambda_functions': []
        }
        
        try:
            clients = self.get_clients(region)
            lex_client = clients['lex']
            lambda_client = clients['lambda']
            
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
            
            # List Lambda functions (this requires additional logic to find associated functions)
            self._debug_print("About to search for Lambda functions...")
            lambda_functions = self._find_lambda_functions_for_bot(bot_id, region, include_fallback=include_fallback, export_bot=export_bot)
            components['lambda_functions'] = lambda_functions
            self._debug_print(f"Lambda functions added to components: {len(lambda_functions)}")
            
        except Exception as e:
            print(f"Error listing bot components: {e}")
        
        return components
    
    def _find_lambda_functions_for_bot(self, bot_id: str, region: str, include_fallback: bool = False, export_bot: bool = False) -> List[Dict[str, Any]]:
        """Find Lambda functions associated with the bot by examining complete bot configuration
        
        Args:
            bot_id: The Lex bot ID
            region: AWS region
            include_fallback: If True, also include functions found by name/description matching
            export_bot: If True, export complete bot definition for comprehensive analysis
        """
        functions = []
        lambda_arns = set()
        lambda_usage = {}  # Track where each Lambda function is used
        
        try:
            clients = self.get_clients(region)
            lex_client = clients['lex']
            lambda_client = clients['lambda']
            
            self._debug_print(f"Starting comprehensive Lambda function search for bot {bot_id} in region {region}")
            
            # First, try to export the complete bot configuration (if requested or in debug mode)
            if export_bot or self.debug:
                bot_export_data = self._export_bot_definition(bot_id, region)
                if bot_export_data:
                    self._debug_print("Successfully exported bot definition - analyzing complete configuration")
                    
                    # Save the bot export for inspection (optional)
                    if self.debug:
                        self._save_bot_export(bot_export_data, bot_id)
                    
                    lambda_arns_from_export = self._extract_lambda_arns_from_export(bot_export_data)
                    for arn, usage_info in lambda_arns_from_export.items():
                        lambda_arns.add(arn)
                        lambda_usage[arn] = usage_info
                    self._debug_print(f"Found {len(lambda_arns_from_export)} Lambda ARNs from bot export")
                else:
                    self._debug_print("Bot export failed, falling back to intent-by-intent analysis")
            else:
                self._debug_print("Bot export not requested, using intent-by-intent analysis")
            
            # Get bot versions for intent-by-intent analysis (fallback/verification)
            versions_response = lex_client.list_bot_versions(botId=bot_id)
            if not versions_response.get('botVersionSummaries'):
                self._debug_print(f"No bot versions found for {bot_id}")
                return functions
                
            latest_version = versions_response['botVersionSummaries'][0]['botVersion']
            self._debug_print(f"Using bot version: {latest_version}")
            
            # Get bot locales
            locales_response = lex_client.list_bot_locales(
                botId=bot_id,
                botVersion=latest_version
            )
            
            if not locales_response.get('botLocaleSummaries'):
                self._debug_print(f"No locales found for bot {bot_id}")
                return functions
            
            self._debug_print(f"Found {len(locales_response['botLocaleSummaries'])} locales")
            
            # Examine each intent for Lambda function ARNs
            for locale in locales_response['botLocaleSummaries']:
                locale_id = locale['localeId']
                self._debug_print(f"Checking locale: {locale_id}")
                
                # List intents
                intents_response = lex_client.list_intents(
                    botId=bot_id,
                    botVersion=latest_version,
                    localeId=locale_id
                )
                
                if not intents_response.get('intentSummaries'):
                    self._debug_print(f"No intents found for locale {locale_id}")
                    continue
                    
                self._debug_print(f"Found {len(intents_response['intentSummaries'])} intents in locale {locale_id}")
                
                # Check each intent for Lambda functions
                for intent in intents_response['intentSummaries']:
                    try:
                        self._debug_print(f"Checking intent: {intent['intentName']}")
                        intent_details = lex_client.describe_intent(
                            botId=bot_id,
                            botVersion=latest_version,
                            localeId=locale_id,
                            intentId=intent['intentId']
                        )
                        
                        # Check fulfillment code hook
                        if 'fulfillmentCodeHook' in intent_details:
                            code_hook = intent_details['fulfillmentCodeHook']
                            self._debug_print(f"Found fulfillment code hook: {code_hook}")
                            if code_hook.get('enabled') and 'lambdaCodeHook' in code_hook:
                                lambda_arn = code_hook['lambdaCodeHook']['lambdaArn']
                                self._debug_print(f"Found Lambda ARN in fulfillment: {lambda_arn}")
                                lambda_arns.add(lambda_arn)
                                
                                # Track usage information
                                if lambda_arn not in lambda_usage:
                                    lambda_usage[lambda_arn] = []
                                lambda_usage[lambda_arn].append({
                                    'intent_name': intent['intentName'],
                                    'locale': locale_id,
                                    'hook_type': 'fulfillment',
                                    'description': 'Handles intent fulfillment (final action)'
                                })
                        
                        # Check dialog code hook
                        if 'dialogCodeHook' in intent_details:
                            dialog_hook = intent_details['dialogCodeHook']
                            self._debug_print(f"Found dialog code hook: {dialog_hook}")
                            if dialog_hook.get('enabled') and 'lambdaCodeHook' in dialog_hook:
                                lambda_arn = dialog_hook['lambdaCodeHook']['lambdaArn']
                                self._debug_print(f"Found Lambda ARN in dialog: {lambda_arn}")
                                lambda_arns.add(lambda_arn)
                                
                                # Track usage information
                                if lambda_arn not in lambda_usage:
                                    lambda_usage[lambda_arn] = []
                                lambda_usage[lambda_arn].append({
                                    'intent_name': intent['intentName'],
                                    'locale': locale_id,
                                    'hook_type': 'dialog',
                                    'description': 'Handles dialog management (slot validation, etc.)'
                                })
                                
                    except Exception as e:
                        self._debug_print(f"Error checking intent {intent['intentName']}: {e}")
            
            self._debug_print(f"Found {len(lambda_arns)} unique Lambda ARNs: {lambda_arns}")
            
            # Get details for each discovered Lambda function
            for lambda_arn in lambda_arns:
                try:
                    function_name = lambda_arn.split(':')[-1]  # Extract function name from ARN
                    function_response = lambda_client.get_function(FunctionName=lambda_arn)
                    
                    functions.append({
                        'name': function_name,
                        'arn': lambda_arn,
                        'description': function_response['Configuration'].get('Description', ''),
                        'runtime': function_response['Configuration']['Runtime'],
                        'region': region,
                        'handler': function_response['Configuration']['Handler'],
                        'code_location': function_response['Code'].get('Location', 'N/A'),
                        'usage': lambda_usage.get(lambda_arn, []),
                        'connection_type': 'direct'  # Directly connected to bot
                    })
                    self._debug_print(f"Added Lambda function: {function_name}")
                except Exception as e:
                    self._debug_print(f"Error getting Lambda function details for {lambda_arn}: {e}")
            
            # Optional fallback search for functions not directly connected
            if include_fallback:
                self._debug_print("Performing fallback Lambda search...")
                try:
                    all_functions = lambda_client.list_functions()
                    self._debug_print(f"Found {len(all_functions['Functions'])} total Lambda functions")
                    
                    for function in all_functions['Functions']:
                        function_name = function['FunctionName']
                        function_arn = function['FunctionArn']
                        
                        # More comprehensive fallback matching
                        name_match = any([
                            'lex' in function_name.lower(),
                            'bot' in function_name.lower(),
                            bot_id.lower() in function_name.lower(),
                            'chatbot' in function_name.lower(),
                            'intent' in function_name.lower()
                        ])
                        
                        desc_match = bot_id in function.get('Description', '')
                        
                        if (name_match or desc_match) and function_arn not in lambda_arns:
                            functions.append({
                                'name': function_name,
                                'arn': function_arn,
                                'description': function.get('Description', ''),
                                'runtime': function['Runtime'],
                                'region': region,
                                'handler': function['Handler'],
                                'code_location': 'N/A',
                                'usage': [],  # No direct usage found
                                'connection_type': 'inferred'  # Inferred from naming/description
                            })
                            self._debug_print(f"Added Lambda function from fallback: {function_name}")
                            
                except Exception as e:
                    self._debug_print(f"Error in fallback Lambda search: {e}")
            else:
                self._debug_print("Only showing directly connected functions (no fallback search)")
            
            # In debug mode, show what functions exist but aren't connected
            if not functions and self.debug:
                self._debug_print("No Lambda functions are directly connected to this bot")
                self._debug_print("Debug mode: Showing available Lambda functions for reference...")
                try:
                    all_functions = lambda_client.list_functions()
                    self._debug_print(f"Available Lambda functions in region {region} (NOT connected to bot):")
                    for function in all_functions['Functions']:
                        self._debug_print(f"  - {function['FunctionName']} ({function['Runtime']})")
                        self._debug_print(f"    Description: {function.get('Description', 'No description')}")
                        self._debug_print(f"    ARN: {function['FunctionArn']}")
                except Exception as e:
                    self._debug_print(f"Error listing all functions: {e}")
                
        except Exception as e:
            self._debug_print(f"Error finding Lambda functions: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
        
        self._debug_print(f"Total Lambda functions found: {len(functions)}")
        return functions
    
    def _export_bot_definition(self, bot_id: str, region: str) -> dict:
        """Export the complete bot definition to analyze all Lambda function references"""
        try:
            clients = self.get_clients(region)
            lex_client = clients['lex']
            
            # Start bot export
            export_response = lex_client.create_export(
                resourceSpecification={
                    'botExportSpecification': {
                        'botId': bot_id,
                        'botVersion': 'DRAFT'
                    }
                },
                fileFormat='JSON'
            )
            
            export_id = export_response['exportId']
            self._debug_print(f"Started bot export with ID: {export_id}")
            
            # Wait for export to complete
            import time
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                status_response = lex_client.describe_export(exportId=export_id)
                export_status = status_response['exportStatus']
                
                if export_status == 'Completed':
                    download_url = status_response['downloadUrl']
                    self._debug_print(f"Export completed. Download URL: {download_url}")
                    
                    # Download and parse the export
                    import requests
                    import zipfile
                    import tempfile
                    import json
                    
                    # Download the export zip
                    response = requests.get(download_url)
                    response.raise_for_status()
                    
                    # Extract and parse the JSON
                    with tempfile.NamedTemporaryFile(suffix='.zip') as temp_zip:
                        temp_zip.write(response.content)
                        temp_zip.flush()
                        
                        with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                            # Look for the bot definition JSON file
                            json_files = [f for f in zip_ref.namelist() if f.endswith('.json')]
                            if json_files:
                                with zip_ref.open(json_files[0]) as json_file:
                                    bot_data = json.load(json_file)
                                    self._debug_print(f"Successfully parsed bot definition from {json_files[0]}")
                                    return bot_data
                    
                elif export_status == 'Failed':
                    self._debug_print(f"Export failed: {status_response.get('failureReasons', 'Unknown error')}")
                    break
                
                time.sleep(10)
                wait_time += 10
                self._debug_print(f"Waiting for export... ({wait_time}s)")
            
            if wait_time >= max_wait:
                self._debug_print("Export timed out after 5 minutes")
                
        except Exception as e:
            self._debug_print(f"Error exporting bot definition: {e}")
        
        return None
    
    def _extract_lambda_arns_from_export(self, bot_data: dict) -> dict:
        """Extract Lambda ARNs from the complete bot export data"""
        lambda_arns_usage = {}
        
        try:
            # Look for Lambda ARNs in the bot definition
            def find_lambda_arns(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        # Check for Lambda ARN patterns
                        if key == 'lambdaArn' and isinstance(value, str) and 'lambda' in value:
                            self._debug_print(f"Found Lambda ARN at {current_path}: {value}")
                            
                            # Extract context information
                            context = self._extract_context_from_path(current_path, obj)
                            
                            if value not in lambda_arns_usage:
                                lambda_arns_usage[value] = []
                            lambda_arns_usage[value].append(context)
                        
                        # Recursively search nested objects
                        find_lambda_arns(value, current_path)
                        
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        find_lambda_arns(item, current_path)
            
            find_lambda_arns(bot_data)
            
            self._debug_print(f"Extracted {len(lambda_arns_usage)} unique Lambda ARNs from bot export")
            for arn, usage_list in lambda_arns_usage.items():
                self._debug_print(f"  {arn}: {len(usage_list)} usage(s)")
            
        except Exception as e:
            self._debug_print(f"Error extracting Lambda ARNs from export: {e}")
        
        return lambda_arns_usage
    
    def _extract_context_from_path(self, path: str, obj: dict) -> dict:
        """Extract context information from the path where Lambda ARN was found"""
        context = {
            'location': path,
            'intent_name': 'Unknown',
            'locale': 'Unknown',
            'hook_type': 'Unknown',
            'description': 'Found in bot export'
        }
        
        # Try to extract more detailed context from the path
        parts = path.split('.')
        
        # Look for locale information
        for i, part in enumerate(parts):
            if 'locale' in part.lower() or len(part) == 5 and '_' in part:  # e.g., en_US
                if i + 1 < len(parts):
                    context['locale'] = parts[i + 1]
                elif part.startswith('locale') and i > 0:
                    context['locale'] = parts[i - 1]
                break
        
        # Look for intent name
        if 'intents' in path:
            for i, part in enumerate(parts):
                if part == 'intents' and i + 1 < len(parts):
                    next_part = parts[i + 1]
                    if '[' in next_part:
                        # Extract from array notation like intents[0]
                        context['intent_name'] = 'Intent_' + next_part.strip('[]')
                    else:
                        context['intent_name'] = next_part
                    break
        
        # Determine hook type and description
        if 'fulfillmentCodeHook' in path:
            context['hook_type'] = 'fulfillment'
            context['description'] = 'Handles intent fulfillment (final action)'
        elif 'dialogCodeHook' in path:
            context['hook_type'] = 'dialog'
            context['description'] = 'Handles dialog management (slot validation, etc.)'
        elif 'confirmationSetting' in path:
            context['hook_type'] = 'confirmation'
            context['description'] = 'Handles confirmation prompts'
        elif 'declinationResponse' in path:
            context['hook_type'] = 'declination'
            context['description'] = 'Handles declination responses'
        elif 'initialResponse' in path:
            context['hook_type'] = 'initial'
            context['description'] = 'Handles initial responses'
        elif 'closingSetting' in path:
            context['hook_type'] = 'closing'
            context['description'] = 'Handles closing responses'
        
        return context
    
    def _save_bot_export(self, bot_data: dict, bot_id: str):
        """Save the bot export data for inspection"""
        try:
            import json
            export_file = self.download_dir / f"{bot_id}_bot_export.json"
            with open(export_file, 'w') as f:
                json.dump(bot_data, f, indent=2, default=str)
            self._debug_print(f"Saved bot export to: {export_file}")
        except Exception as e:
            self._debug_print(f"Error saving bot export: {e}")
    
    def display_lambda_usage_summary(self, functions: List[Dict[str, Any]]):
        """Display a summary of Lambda function usage"""
        if not functions:
            print("No Lambda functions found for this bot.")
            return
            
        print(f"\n{'='*60}")
        print("LAMBDA FUNCTION USAGE SUMMARY")
        print(f"{'='*60}")
        
        # Separate direct connections from inferred ones
        direct_functions = [f for f in functions if f.get('connection_type') == 'direct']
        inferred_functions = [f for f in functions if f.get('connection_type') == 'inferred']
        
        if direct_functions:
            print(f"\n🔗 DIRECTLY CONNECTED FUNCTIONS ({len(direct_functions)}):")
            print("These functions are actively used by the bot")
            print("-" * 60)
        
        for func in direct_functions:
            self._display_function_details(func)
        
        if inferred_functions:
            print(f"\n🔍 POTENTIALLY RELATED FUNCTIONS ({len(inferred_functions)}):")
            print("These functions were found by name/description matching")
            print("-" * 60)
        
        for func in inferred_functions:
            self._display_function_details(func)
        
        if not direct_functions and not inferred_functions:
            print("\n❌ No Lambda functions found for this bot.")
            print("This could mean:")
            print("  - The bot doesn't use Lambda functions")
            print("  - Lambda functions are not properly configured in intents")
            print("  - Use --include-fallback to search for potentially related functions")
        
        print(f"\n{'='*60}")
        print("HOOK TYPE EXPLANATIONS:")
        print("🎯 Fulfillment: Handles the final action after all slots are filled")
        print("💬 Dialog: Manages conversation flow and slot validation")
        print(f"{'='*60}")
    
    def _display_function_details(self, func: Dict[str, Any]):
        """Display details for a single Lambda function"""
        print(f"\n📋 Function: {func['name']}")
        print(f"   Runtime: {func['runtime']}")
        print(f"   Handler: {func['handler']}")
        print(f"   Description: {func.get('description', 'No description')}")
        
        usage = func.get('usage', [])
        if usage:
            print(f"   Used in {len(usage)} location(s):")
            for use in usage:
                intent_name = use['intent_name']
                hook_type = use['hook_type']
                description = use['description']
                locale_info = use['locale']
                
                if hook_type == 'fulfillment':
                    icon = "🎯"
                elif hook_type == 'dialog':
                    icon = "💬"
                else:
                    icon = "⚙️"
                
                print(f"     {icon} Intent: {intent_name} ({hook_type})")
                print(f"        Purpose: {description}")
                print(f"        Locale: {locale_info}")
        else:
            connection_type = func.get('connection_type', 'unknown')
            if connection_type == 'direct':
                print(f"   ⚠️  Connected to bot but no specific intent usage found")
            elif connection_type == 'inferred':
                print(f"   🔍 Potentially related (name/description match)")
            elif connection_type == 'debug':
                print(f"   🐛 Debug mode - verify connection manually")
            else:
                print(f"   ❓ Unknown connection")
    
    def _download_lambda_code(self, component: Dict[str, Any], lambda_client, type_dir: Path) -> Dict[str, Any]:
        """Download Lambda function source code"""
        import zipfile
        import tempfile
        import os
        
        try:
            # Get the function code
            response = lambda_client.get_function(
                FunctionName=component['arn']
            )
            
            # Download code from the presigned URL
            code_location = response['Code'].get('Location')
            if code_location:
                import requests
                
                # Create a subdirectory for the function code
                code_dir = type_dir / f"{component['name']}_code"
                code_dir.mkdir(exist_ok=True)
                
                # Download the zip file
                zip_response = requests.get(code_location)
                zip_response.raise_for_status()
                
                # Save and extract the zip file
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                    temp_zip.write(zip_response.content)
                    temp_zip_path = temp_zip.name
                
                try:
                    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                        zip_ref.extractall(code_dir)
                    
                    print(f"Lambda code extracted to: {code_dir}")
                    
                    return {
                        'code_extracted': True,
                        'code_directory': str(code_dir),
                        'files_extracted': os.listdir(code_dir)
                    }
                finally:
                    os.unlink(temp_zip_path)
            else:
                return {
                    'code_extracted': False,
                    'reason': 'No code location available'
                }
                
        except Exception as e:
            print(f"Error downloading Lambda code: {e}")
            return {
                'code_extracted': False,
                'reason': str(e)
            }
    
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
            locale = item.get('locale', 'N/A')
            
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
            lambda_client = clients['lambda']
            
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
                
            elif component_type == 'lambda_functions':
                # Download both configuration and code
                function_response = lambda_client.get_function(
                    FunctionName=component['arn']
                )
                
                # Save configuration
                config_content = self._clean_lambda_response(function_response)
                
                # Download source code if available
                code_content = self._download_lambda_code(component, lambda_client, type_dir)
                
                # Combine config and code info
                content = {
                    'configuration': config_content,
                    'code_info': {
                        'location': function_response['Code'].get('Location', 'N/A'),
                        'repository_type': function_response['Code'].get('RepositoryType', 'N/A'),
                        'code_sha256': function_response['Configuration'].get('CodeSha256', 'N/A'),
                        'code_size': function_response['Configuration'].get('CodeSize', 0)
                    }
                }
            
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
    
    def _clean_lambda_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Clean Lambda response for editing"""
        function_config = response['Configuration']
        keys_to_keep = [
            'FunctionName', 'Description', 'Runtime', 'Handler', 'Environment',
            'Timeout', 'MemorySize', 'DeadLetterConfig', 'TracingConfig'
        ]
        return {k: v for k, v in function_config.items() if k in keys_to_keep}
    
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
            elif component_type == 'lambda_functions':
                return self._upload_lambda(content, region)
            
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
    
    def _upload_lambda(self, content: Dict[str, Any], region: str) -> bool:
        """Upload Lambda function configuration and code"""
        try:
            clients = self.get_clients(region)
            lambda_client = clients['lambda']
            
            if 'configuration' in content:
                config = content['configuration']
                function_name = config['FunctionName']
                
                # Update function configuration
                response = lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    **{k: v for k, v in config.items() if k != 'FunctionName'}
                )
                print(f"Successfully updated Lambda function configuration: {function_name}")
                
                # Check if there's code to upload
                if 'code_info' in content and content['code_info'].get('code_directory'):
                    code_dir = content['code_info']['code_directory']
                    if os.path.exists(code_dir):
                        success = self._upload_lambda_code(function_name, code_dir, lambda_client)
                        if success:
                            print(f"Successfully updated Lambda function code: {function_name}")
                        else:
                            print(f"Warning: Failed to update code for: {function_name}")
                
                return True
            else:
                # Legacy format support
                function_name = content['FunctionName']
                response = lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    **{k: v for k, v in content.items() if k != 'FunctionName'}
                )
                print(f"Successfully updated Lambda function: {function_name}")
                return True
                
        except Exception as e:
            print(f"Error updating Lambda function: {e}")
            return False
    
    def _upload_lambda_code(self, function_name: str, code_dir: str, lambda_client) -> bool:
        """Upload Lambda function source code"""
        import zipfile
        import tempfile
        import os
        
        try:
            # Create a zip file with the code
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
            
            try:
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for root, dirs, files in os.walk(code_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, code_dir)
                            zip_file.write(file_path, arcname)
                
                # Upload the zip file
                with open(temp_zip_path, 'rb') as zip_file:
                    response = lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_file.read()
                    )
                
                return True
                
            finally:
                os.unlink(temp_zip_path)
                
        except Exception as e:
            print(f"Error uploading Lambda code: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Amazon Lex Bot Manager')
    parser.add_argument('--csv', default='bot_ids.csv', help='CSV file containing bot IDs (default: bot_ids.csv)')
    parser.add_argument('--upload', help='Upload a modified component file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--include-fallback', action='store_true', help='Include Lambda functions found by name/description matching (not just directly connected ones)')
    parser.add_argument('--export-bot', action='store_true', help='Export complete bot definition for comprehensive Lambda analysis')
    
    args = parser.parse_args()
    
    manager = LexBotManager(debug=args.debug)
    
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
            components = manager.list_bot_components(bot_id, region, include_fallback=args.include_fallback, export_bot=args.export_bot)
            
            # Show Lambda usage summary if any Lambda functions were found
            if components['lambda_functions']:
                manager.display_lambda_usage_summary(components['lambda_functions'])
            
            while True:
                selected_component = manager.display_selection_menu(components)
                if selected_component is None:
                    break
                
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