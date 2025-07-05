#!/usr/bin/env python3
"""
Script to get all necessary IDs for Amazon Lex Bot operations.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError

def get_lex_v2_info():
    """Get information from Lex V2."""
    try:
        client = boto3.client('lexv2-models')
        
        print("🔍 Amazon Lex V2 Information")
        print("=" * 50)
        
        # List all bots
        print("📋 Available Bots:")
        print("-" * 30)
        
        try:
            response = client.list_bots()
            bots = response.get('botSummaries', [])
            
            if not bots:
                print("❌ No bots found in Lex V2")
                return None
            
            for i, bot in enumerate(bots, 1):
                print(f"{i}. Bot Name: {bot['botName']}")
                print(f"   Bot ID: {bot['botId']}")
                print(f"   Status: {bot['botStatus']}")
                print(f"   Description: {bot.get('description', 'N/A')}")
                print()
            
            # If there's only one bot, automatically select it
            if len(bots) == 1:
                selected_bot = bots[0]
                print(f"🎯 Auto-selecting the only bot: {selected_bot['botName']}")
            else:
                # Ask user to select a bot
                while True:
                    try:
                        choice = input(f"Select a bot (1-{len(bots)}): ")
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(bots):
                            selected_bot = bots[choice_idx]
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(bots)}")
                    except ValueError:
                        print("Please enter a valid number")
            
            bot_id = selected_bot['botId']
            bot_name = selected_bot['botName']
            
            print(f"\n🤖 Selected Bot: {bot_name}")
            print(f"🆔 Bot ID: {bot_id}")
            print("=" * 50)
            
            # Get locales for the selected bot
            print("🌐 Available Locales:")
            print("-" * 30)
            
            locales_response = client.list_bot_locales(
                botId=bot_id,
                botVersion='DRAFT'
            )
            
            locales = locales_response.get('botLocaleSummaries', [])
            
            if not locales:
                print("❌ No locales found for this bot")
                return None
            
            for locale in locales:
                print(f"Locale: {locale['localeId']} ({locale['localeName']})")
            
            # Use the first locale or let user choose
            selected_locale = locales[0]['localeId']
            print(f"🎯 Using locale: {selected_locale}")
            
            # Get intents for the selected bot and locale
            print(f"\n📝 Intents in {selected_locale}:")
            print("-" * 30)
            
            intents_response = client.list_intents(
                botId=bot_id,
                botVersion='DRAFT',
                localeId=selected_locale
            )
            
            intents = intents_response.get('intentSummaries', [])
            
            if intents:
                for intent in intents:
                    print(f"Intent Name: {intent['intentName']}")
                    print(f"Intent ID: {intent['intentId']}")
                    print(f"Description: {intent.get('description', 'N/A')}")
                    print()
            else:
                print("❌ No intents found")
            
            # Get slot types
            print(f"🎰 Slot Types in {selected_locale}:")
            print("-" * 30)
            
            slot_types_response = client.list_slot_types(
                botId=bot_id,
                botVersion='DRAFT',
                localeId=selected_locale
            )
            
            slot_types = slot_types_response.get('slotTypeSummaries', [])
            
            if slot_types:
                for slot_type in slot_types:
                    print(f"Slot Type Name: {slot_type['slotTypeName']}")
                    print(f"Slot Type ID: {slot_type['slotTypeId']}")
                    print(f"Description: {slot_type.get('description', 'N/A')}")
                    print()
                    
                    # If this is the DishType slot, show some details
                    if slot_type['slotTypeName'] == 'DishType':
                        print("🍽️  Found DishType slot type!")
                        print(f"   ID to use: {slot_type['slotTypeId']}")
                        print()
            else:
                print("❌ No slot types found")
            
            return {
                'bot_id': bot_id,
                'bot_name': bot_name,
                'locale_id': selected_locale,
                'intents': intents,
                'slot_types': slot_types
            }
            
        except ClientError as e:
            print(f"❌ Error accessing Lex V2: {e}")
            return None
            
    except NoCredentialsError:
        print("❌ Error: AWS credentials not configured")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def get_lex_v1_info():
    """Get information from Lex V1."""
    try:
        client = boto3.client('lex-models')
        
        print("\n🔍 Amazon Lex V1 Information")
        print("=" * 50)
        
        # List intents
        print("📝 Available Intents:")
        print("-" * 30)
        
        intents_response = client.get_intents()
        intents = intents_response.get('intents', [])
        
        if intents:
            for intent in intents:
                print(f"Intent Name: {intent['name']}")
                print(f"Version: {intent['version']}")
                print(f"Description: {intent.get('description', 'N/A')}")
                print()
        else:
            print("❌ No intents found in Lex V1")
        
        # List slot types
        print("🎰 Available Slot Types:")
        print("-" * 30)
        
        slot_types_response = client.get_slot_types()
        slot_types = slot_types_response.get('slotTypes', [])
        
        if slot_types:
            for slot_type in slot_types:
                print(f"Slot Type Name: {slot_type['name']}")
                print(f"Version: {slot_type['version']}")
                print(f"Description: {slot_type.get('description', 'N/A')}")
                print()
        else:
            print("❌ No slot types found in Lex V1")
            
        return {
            'intents': intents,
            'slot_types': slot_types
        }
        
    except ClientError as e:
        print(f"❌ Error accessing Lex V1: {e}")
        return None

def generate_commands(v2_info):
    """Generate AWS CLI commands based on the retrieved information."""
    if not v2_info:
        return
    
    print("\n🛠️  Generated AWS CLI Commands")
    print("=" * 50)
    
    bot_id = v2_info['bot_id']
    locale_id = v2_info['locale_id']
    
    # Find DishType slot type ID
    dish_type_slot_id = None
    for slot_type in v2_info['slot_types']:
        if slot_type['slotTypeName'] == 'DishType':
            dish_type_slot_id = slot_type['slotTypeId']
            break
    
    if dish_type_slot_id:
        print("✅ Found DishType slot type!")
        print(f"🎯 Slot Type ID: {dish_type_slot_id}")
        print()
    
    # Find an intent ID (use first one as example)
    intent_id = None
    intent_name = None
    if v2_info['intents']:
        intent_id = v2_info['intents'][0]['intentId']
        intent_name = v2_info['intents'][0]['intentName']
    
    print("📋 Command to update an intent:")
    print("-" * 40)
    
    if intent_id and dish_type_slot_id:
        command = f"""aws lexv2-models update-intent \\
    --bot-id "{bot_id}" \\
    --bot-version "DRAFT" \\
    --locale-id "{locale_id}" \\
    --intent-id "{intent_id}" \\
    --intent-name "{intent_name}" \\
    --description "Updated intent for ordering dishes" \\
    --sample-utterances '[
        {{
            "utterance": "I want to order {{DishType}}"
        }},
        {{
            "utterance": "Can I get {{DishType}}"
        }}
    ]' \\
    --slots '[
        {{
            "slotName": "DishType",
            "description": "Type of dish to order",
            "slotTypeId": "{dish_type_slot_id}",
            "valueElicitationSetting": {{
                "slotConstraint": "Required",
                "promptSpecification": {{
                    "messageGroups": [
                        {{
                            "message": {{
                                "plainTextMessage": {{
                                    "value": "What dish would you like to order?"
                                }}
                            }}
                        }}
                    ],
                    "maxRetries": 3
                }}
            }}
        }}
    ]'"""
        print(command)
    else:
        print("❌ Missing required IDs to generate complete command")
        print(f"Bot ID: {bot_id}")
        print(f"Locale ID: {locale_id}")
        print(f"Intent ID: {intent_id if intent_id else 'NOT FOUND'}")
        print(f"DishType Slot ID: {dish_type_slot_id if dish_type_slot_id else 'NOT FOUND'}")

def main():
    """Main execution function."""
    print("🚀 AWS Lex Bot ID Retrieval Tool")
    print("=" * 50)
    
    # Try Lex V2 first (recommended)
    v2_info = get_lex_v2_info()
    
    # Also show V1 info if available
    v1_info = get_lex_v1_info()
    
    # Generate commands if we have V2 info
    if v2_info:
        generate_commands(v2_info)
    
    print("\n" + "=" * 50)
    print("ℹ️  Next Steps:")
    print("1. Copy the generated command above")
    print("2. Modify the intent details as needed")
    print("3. Run the command to update your intent")
    print("4. Build your bot with: aws lexv2-models build-bot-locale")

if __name__ == "__main__":
    main()