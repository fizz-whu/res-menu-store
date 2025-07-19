#!/usr/bin/env python3
"""
Bot Data Exporter - Extract all bot components and organize into folders
"""

import boto3
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError


class BotExporter:
    def __init__(self, bot_id, output_dir="bot_export"):
        self.bot_id = bot_id
        self.output_dir = Path(output_dir)
        self.lexv2_client = boto3.client('lexv2-models')
        self.lambda_client = boto3.client('lambda')
        
        # Create output directory structure
        self.create_output_structure()
    
    def create_output_structure(self):
        """Create organized folder structure for bot export"""
        folders = [
            'intents',
            'slots', 
            'lambda_functions',
            'bot_config',
            'test_data',
            'documentation'
        ]
        
        for folder in folders:
            (self.output_dir / folder).mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Created export directory structure at: {self.output_dir}")
    
    def export_bot_config(self, locale_id='en_US'):
        """Export main bot configuration"""
        try:
            # Get bot details
            bot_response = self.lexv2_client.describe_bot(botId=self.bot_id)
            
            # Get bot locale details
            locale_response = self.lexv2_client.describe_bot_locale(
                botId=self.bot_id,
                botVersion='DRAFT',
                localeId=locale_id
            )
            
            # Combine bot and locale info
            bot_config = {
                'bot_info': bot_response,
                'locale_info': locale_response,
                'export_timestamp': datetime.now().isoformat(),
                'bot_id': self.bot_id,
                'locale_id': locale_id
            }
            
            # Save to file
            config_file = self.output_dir / 'bot_config' / f'{self.bot_id}_config.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(bot_config, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Exported bot config to: {config_file}")
            return bot_config
            
        except ClientError as e:
            print(f"❌ Error exporting bot config: {e}")
            return None
    
    def export_intents(self, locale_id='en_US'):
        """Export all intents with their complete definitions"""
        try:
            # List all intents
            intents_response = self.lexv2_client.list_intents(
                botId=self.bot_id,
                botVersion='DRAFT',
                localeId=locale_id
            )
            
            intents = intents_response.get('intentSummaries', [])
            exported_intents = {}
            
            for intent_summary in intents:
                intent_id = intent_summary['intentId']
                intent_name = intent_summary['intentName']
                
                # Get detailed intent information
                intent_detail = self.lexv2_client.describe_intent(
                    botId=self.bot_id,
                    botVersion='DRAFT',
                    localeId=locale_id,
                    intentId=intent_id
                )
                
                exported_intents[intent_name] = intent_detail
                
                # Save individual intent file
                intent_file = self.output_dir / 'intents' / f'{intent_name}.json'
                with open(intent_file, 'w', encoding='utf-8') as f:
                    json.dump(intent_detail, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"✅ Exported intent: {intent_name}")
            
            # Save all intents in one file
            all_intents_file = self.output_dir / 'intents' / 'all_intents.json'
            with open(all_intents_file, 'w', encoding='utf-8') as f:
                json.dump(exported_intents, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Exported {len(intents)} intents to: {self.output_dir / 'intents'}")
            return exported_intents
            
        except ClientError as e:
            print(f"❌ Error exporting intents: {e}")
            return {}
    
    def export_slot_types(self, locale_id='en_US'):
        """Export all slot types with their values"""
        try:
            # List all slot types
            slot_types_response = self.lexv2_client.list_slot_types(
                botId=self.bot_id,
                botVersion='DRAFT',
                localeId=locale_id
            )
            
            slot_types = slot_types_response.get('slotTypeSummaries', [])
            exported_slots = {}
            
            for slot_summary in slot_types:
                slot_type_id = slot_summary['slotTypeId']
                slot_type_name = slot_summary['slotTypeName']
                
                # Get detailed slot type information
                slot_detail = self.lexv2_client.describe_slot_type(
                    botId=self.bot_id,
                    botVersion='DRAFT',
                    localeId=locale_id,
                    slotTypeId=slot_type_id
                )
                
                exported_slots[slot_type_name] = slot_detail
                
                # Save individual slot type file
                slot_file = self.output_dir / 'slots' / f'{slot_type_name}.json'
                with open(slot_file, 'w', encoding='utf-8') as f:
                    json.dump(slot_detail, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"✅ Exported slot type: {slot_type_name}")
            
            # Save all slots in one file
            all_slots_file = self.output_dir / 'slots' / 'all_slot_types.json'
            with open(all_slots_file, 'w', encoding='utf-8') as f:
                json.dump(exported_slots, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Exported {len(slot_types)} slot types to: {self.output_dir / 'slots'}")
            return exported_slots
            
        except ClientError as e:
            print(f"❌ Error exporting slot types: {e}")
            return {}
    
    def export_lambda_functions(self, function_names=None):
        """Export Lambda function code and configuration"""
        try:
            if function_names is None:
                # Try to detect lambda functions from bot config or use common names
                function_names = ['cnres-order-processor', 'lex-fulfillment', 'bot-fulfillment']
            
            exported_functions = {}
            
            for function_name in function_names:
                try:
                    # Get function configuration
                    config_response = self.lambda_client.get_function(
                        FunctionName=function_name
                    )
                    
                    # Get function code
                    code_response = self.lambda_client.get_function(
                        FunctionName=function_name,
                        Qualifier='$LATEST'
                    )
                    
                    function_data = {
                        'configuration': config_response['Configuration'],
                        'code_location': code_response['Code'],
                        'export_timestamp': datetime.now().isoformat()
                    }
                    
                    exported_functions[function_name] = function_data
                    
                    # Save individual function file
                    function_file = self.output_dir / 'lambda_functions' / f'{function_name}.json'
                    with open(function_file, 'w', encoding='utf-8') as f:
                        json.dump(function_data, f, indent=2, ensure_ascii=False, default=str)
                    
                    print(f"✅ Exported Lambda function: {function_name}")
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                        print(f"⚠️  Lambda function not found: {function_name}")
                    else:
                        print(f"❌ Error exporting Lambda function {function_name}: {e}")
            
            # Save all functions summary
            if exported_functions:
                all_functions_file = self.output_dir / 'lambda_functions' / 'all_functions.json'
                with open(all_functions_file, 'w', encoding='utf-8') as f:
                    json.dump(exported_functions, f, indent=2, ensure_ascii=False, default=str)
            
            return exported_functions
            
        except Exception as e:
            print(f"❌ Error exporting Lambda functions: {e}")
            return {}
    
    def copy_existing_files(self, source_dir=None):
        """Copy existing bot-related files from the project"""
        if source_dir is None:
            source_dir = Path('/home/fizz/work/res-menu-store')
        else:
            source_dir = Path(source_dir)
        
        # Files to copy
        files_to_copy = [
            ('lambda_function_fixed.py', 'lambda_functions/lambda_function_fixed.py'),
            ('get_lex_ids.py', 'documentation/get_lex_ids.py'),
            ('update_lex_slots.py', 'documentation/update_lex_slots.py'),
            ('scripts/DishType.json', 'slots/DishType_local.json'),
            ('scripts/CustomizationType.json', 'slots/CustomizationType_local.json'),
            ('scripts/OrderFood_intent.json', 'intents/OrderFood_local.json'),
            ('intents/RestaurantInfoIntent.json', 'intents/RestaurantInfoIntent_local.json'),
            ('core_intents/info.txt', 'documentation/intents_planning.txt')
        ]
        
        for source_file, dest_file in files_to_copy:
            source_path = source_dir / source_file
            dest_path = self.output_dir / dest_file
            
            if source_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(source_path, dest_path)
                print(f"✅ Copied: {source_file} -> {dest_file}")
            else:
                print(f"⚠️  File not found: {source_path}")
    
    def generate_summary_report(self):
        """Generate a summary report of the export"""
        summary = {
            'export_info': {
                'bot_id': self.bot_id,
                'export_timestamp': datetime.now().isoformat(),
                'export_directory': str(self.output_dir.absolute())
            },
            'files_exported': {
                'intents': len(list((self.output_dir / 'intents').glob('*.json'))),
                'slots': len(list((self.output_dir / 'slots').glob('*.json'))),
                'lambda_functions': len(list((self.output_dir / 'lambda_functions').glob('*.json'))),
                'config_files': len(list((self.output_dir / 'bot_config').glob('*.json')))
            }
        }
        
        # Save summary report
        summary_file = self.output_dir / 'export_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Create README
        readme_content = f"""# Bot Export for {self.bot_id}

## Export Summary
- **Bot ID**: {self.bot_id}
- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Export Directory**: {self.output_dir.absolute()}

## Directory Structure
```
{self.output_dir.name}/
├── intents/           # All bot intents (JSON format)
├── slots/             # All slot types (JSON format)  
├── lambda_functions/  # Lambda function configurations
├── bot_config/        # Main bot configuration
├── test_data/         # Test utterances and data
├── documentation/     # Project documentation and scripts
└── export_summary.json
```

## Files Exported
- **Intents**: {summary['files_exported']['intents']} files
- **Slot Types**: {summary['files_exported']['slots']} files
- **Lambda Functions**: {summary['files_exported']['lambda_functions']} files
- **Config Files**: {summary['files_exported']['config_files']} files

## Usage
Use these files to:
1. Recreate the bot in another AWS account
2. Version control your bot configuration
3. Backup your bot data
4. Analyze bot structure and components

## Tools
- Use `get_lex_ids.py` to retrieve bot information
- Use `update_lex_slots.py` to update slot types
- Lambda function code is in `lambda_functions/`
"""
        
        readme_file = self.output_dir / 'README.md'
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ Generated summary report: {summary_file}")
        print(f"✅ Generated README: {readme_file}")
        
        return summary
    
    def export_all(self, locale_id='en_US', lambda_functions=None):
        """Export all bot components"""
        print(f"🚀 Starting export for Bot ID: {self.bot_id}")
        print(f"📁 Export directory: {self.output_dir.absolute()}")
        print("=" * 60)
        
        # Export bot configuration
        print("\n📋 Exporting bot configuration...")
        bot_config = self.export_bot_config(locale_id)
        
        # Export intents
        print("\n📝 Exporting intents...")
        intents = self.export_intents(locale_id)
        
        # Export slot types
        print("\n🎰 Exporting slot types...")
        slots = self.export_slot_types(locale_id)
        
        # Export Lambda functions
        print("\n⚡ Exporting Lambda functions...")
        lambda_funcs = self.export_lambda_functions(lambda_functions)
        
        # Copy existing project files
        print("\n📂 Copying existing project files...")
        self.copy_existing_files()
        
        # Generate summary report
        print("\n📊 Generating summary report...")
        summary = self.generate_summary_report()
        
        print("\n" + "=" * 60)
        print("✅ Export completed successfully!")
        print(f"📁 All files saved to: {self.output_dir.absolute()}")
        print(f"📋 {summary['files_exported']['intents']} intents exported")
        print(f"🎰 {summary['files_exported']['slots']} slot types exported")
        print(f"⚡ {summary['files_exported']['lambda_functions']} Lambda functions exported")


def main():
    """Main execution function"""
    print("🤖 Bot Data Exporter")
    print("=" * 60)
    
    # Get bot ID from command line or prompt user
    if len(sys.argv) > 1:
        bot_id = sys.argv[1]
    else:
        bot_id = input("Enter Bot ID (e.g., RWRKZUM7UP): ").strip()
        
        if not bot_id:
            print("❌ Bot ID is required")
            sys.exit(1)
    
    # Optional: custom output directory
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = f"bot_export_{bot_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Optional: locale
    locale_id = sys.argv[3] if len(sys.argv) > 3 else 'en_US'
    
    try:
        # Create exporter and run export
        exporter = BotExporter(bot_id, output_dir)
        exporter.export_all(locale_id)
        
    except NoCredentialsError:
        print("❌ Error: AWS credentials not configured")
        print("Please configure AWS credentials using:")
        print("  aws configure")
        print("  or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()