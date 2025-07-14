#!/usr/bin/env python3
"""
Script to update Amazon Lex slot types using boto3
"""

import boto3
import json
from typing import Dict, Any

def load_slot_data(file_path: str) -> Dict[str, Any]:
    """Load slot type data from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_slot_type(lex_client, bot_id: str, bot_version: str, locale_id: str, 
                     slot_type_id: str, slot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a slot type in Amazon Lex"""
    
    response = lex_client.update_slot_type(
        botId=bot_id,
        botVersion=bot_version,
        localeId=locale_id,
        slotTypeId=slot_type_id,
        slotTypeName=slot_data['slotTypeName'],
        description=slot_data['description'],
        slotTypeValues=slot_data['slotTypeValues'],
        valueSelectionSetting=slot_data['valueSelectionSetting']
    )
    
    return response

def main():
    # Configuration - Update these values
    BOT_ID = "RWRKZUM7UP"  # Replace with your bot ID
    BOT_VERSION = "DRAFT"
    LOCALE_ID = "en_US"
    
    # Slot type IDs - Replace with your actual slot type IDs
    DISH_TYPE_SLOT_ID = "CBBKGFMKCU"
    CUSTOMIZATION_TYPE_SLOT_ID = "2JOI5P43LW"
    
    # Initialize Lex client
    lex_client = boto3.client('lexv2-models')
    
    try:
        # Update DishType slot
        print("Loading DishType slot data...")
        dish_type_data = load_slot_data('scripts/CnRes001_slot_type_DishType_v2.json')
        
        print("Updating DishType slot...")
        dish_response = update_slot_type(
            lex_client, BOT_ID, BOT_VERSION, LOCALE_ID, 
            DISH_TYPE_SLOT_ID, dish_type_data
        )
        print(f"✓ DishType slot updated successfully. Slot Type ID: {dish_response['slotTypeId']}")
        
        # Update CustomizationType slot
        print("\nLoading CustomizationType slot data...")
        customization_data = load_slot_data('scripts/CnRes001_slot_type_CustomizationType_v2.json')
        
        print("Updating CustomizationType slot...")
        customization_response = update_slot_type(
            lex_client, BOT_ID, BOT_VERSION, LOCALE_ID,
            CUSTOMIZATION_TYPE_SLOT_ID, customization_data
        )
        print(f"✓ CustomizationType slot updated successfully. Slot Type ID: {customization_response['slotTypeId']}")
        
        print("\n🎉 All slot types updated successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find file - {e}")
    except Exception as e:
        print(f"❌ Error updating slot types: {e}")

def list_slot_types(bot_id: str, bot_version: str = "DRAFT", locale_id: str = "en_US"):
    """Helper function to list existing slot types"""
    lex_client = boto3.client('lexv2-models')
    
    try:
        response = lex_client.list_slot_types(
            botId=bot_id,
            botVersion=bot_version,
            localeId=locale_id
        )
        
        print("Existing slot types:")
        for slot in response['slotTypeSummaries']:
            print(f"  - Name: {slot['slotTypeName']}, ID: {slot['slotTypeId']}")
            
    except Exception as e:
        print(f"❌ Error listing slot types: {e}")

if __name__ == "__main__":
    # Uncomment the line below to list existing slot types first
    # list_slot_types("YOUR_BOT_ID")
    
    main()