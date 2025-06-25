#!/usr/bin/env python3
"""
Universal script to clean up slot type JSON files:
1. If any synonym value contains '_' or a number, make synonyms an empty list
2. Replace all 'w/' with 'with' in all values and synonyms
3. Works with both CustomizationType and DishType files
"""

import json
import re
import os
import sys

def contains_underscore_or_number(text):
    """Check if text contains underscore or any digit"""
    return '_' in text or any(char.isdigit() for char in text)

def replace_w_with_with(text):
    """Replace 'w/' with 'with' in text"""
    return text.replace('w/', 'with')

def clean_customization_type_file(data):
    """Clean CustomizationType format file"""
    modifications_made = 0
    
    for slot_value in data.get('slotTypeValues', []):
        # Process main sample value
        if 'sampleValue' in slot_value and 'value' in slot_value['sampleValue']:
            original_value = slot_value['sampleValue']['value']
            new_value = replace_w_with_with(original_value)
            if new_value != original_value:
                slot_value['sampleValue']['value'] = new_value
                print(f"Updated sample value: '{original_value}' -> '{new_value}'")
                modifications_made += 1
        
        # Process synonyms
        if 'synonyms' in slot_value:
            should_clear_synonyms = False
            
            for synonym in slot_value['synonyms']:
                if 'value' in synonym:
                    synonym_value = synonym['value']
                    if contains_underscore_or_number(synonym_value):
                        should_clear_synonyms = True
                        print(f"Found problematic synonym '{synonym_value}' - will clear all synonyms for this slot")
                        break
            
            if should_clear_synonyms:
                slot_value['synonyms'] = []
                modifications_made += 1
                print(f"Cleared synonyms for slot value: {slot_value['sampleValue']['value']}")
            else:
                for synonym in slot_value['synonyms']:
                    if 'value' in synonym:
                        original_synonym = synonym['value']
                        new_synonym = replace_w_with_with(original_synonym)
                        if new_synonym != original_synonym:
                            synonym['value'] = new_synonym
                            print(f"Updated synonym: '{original_synonym}' -> '{new_synonym}'")
                            modifications_made += 1
    
    return modifications_made

def clean_dish_type_file(data):
    """Clean DishType format file"""
    modifications_made = 0
    
    for slot_value in data.get('slotTypeValues', []):
        # Process main sample value
        if 'sampleValue' in slot_value and 'value' in slot_value['sampleValue']:
            original_value = slot_value['sampleValue']['value']
            new_value = replace_w_with_with(original_value)
            if new_value != original_value:
                slot_value['sampleValue']['value'] = new_value
                print(f"Updated sample value: '{original_value}' -> '{new_value}'")
                modifications_made += 1
        
        # Process synonyms
        if 'synonyms' in slot_value:
            should_clear_synonyms = False
            
            for synonym in slot_value['synonyms']:
                if 'value' in synonym:
                    synonym_value = synonym['value']
                    if contains_underscore_or_number(synonym_value):
                        should_clear_synonyms = True
                        print(f"Found problematic synonym '{synonym_value}' - will clear all synonyms for this slot")
                        break
            
            if should_clear_synonyms:
                slot_value['synonyms'] = []
                modifications_made += 1
                print(f"Cleared synonyms for slot value: {slot_value['sampleValue']['value']}")
            else:
                for synonym in slot_value['synonyms']:
                    if 'value' in synonym:
                        original_synonym = synonym['value']
                        new_synonym = replace_w_with_with(original_synonym)
                        if new_synonym != original_synonym:
                            synonym['value'] = new_synonym
                            print(f"Updated synonym: '{original_synonym}' -> '{new_synonym}'")
                            modifications_made += 1
    
    return modifications_made

def clean_old_format_file(data):
    """Clean old format file (with values array directly)"""
    modifications_made = 0
    
    for slot_value in data.get('values', []):
        # Process main value
        if 'value' in slot_value:
            original_value = slot_value['value']
            new_value = replace_w_with_with(original_value)
            if new_value != original_value:
                slot_value['value'] = new_value
                print(f"Updated value: '{original_value}' -> '{new_value}'")
                modifications_made += 1
        
        # Process synonyms
        if 'synonyms' in slot_value:
            should_clear_synonyms = False
            
            for synonym_value in slot_value['synonyms']:
                if contains_underscore_or_number(synonym_value):
                    should_clear_synonyms = True
                    print(f"Found problematic synonym '{synonym_value}' - will clear all synonyms for this slot")
                    break
            
            if should_clear_synonyms:
                slot_value['synonyms'] = []
                modifications_made += 1
                print(f"Cleared synonyms for value: {slot_value['value']}")
            else:
                for i, synonym_value in enumerate(slot_value['synonyms']):
                    new_synonym = replace_w_with_with(synonym_value)
                    if new_synonym != synonym_value:
                        slot_value['synonyms'][i] = new_synonym
                        print(f"Updated synonym: '{synonym_value}' -> '{new_synonym}'")
                        modifications_made += 1
    
    return modifications_made

def clean_slot_type_file(file_path):
    """Clean any slot type JSON file"""
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Processing file: {file_path}")
        
        # Determine file format and process accordingly
        if 'slotTypeValues' in data:
            # New format (v2 files)
            modifications_made = clean_customization_type_file(data)
        elif 'values' in data:
            # Old format
            modifications_made = clean_old_format_file(data)
        else:
            print("Warning: Unknown file format")
            return False
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Total modifications made: {modifications_made}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # File path provided as argument
        file_paths = sys.argv[1:]
    else:
        # Default files
        file_paths = [
            "/Users/fizz/work/res-menu-store/scripts/CnRes001_slot_type_CustomizationType_v2.json",
            "/Users/fizz/work/res-menu-store/scripts/CnRes001_slot_type_DishType_v2.json"
        ]
    
    print("Starting cleanup of slot type files...")
    print("=" * 60)
    
    success_count = 0
    for file_path in file_paths:
        print(f"\nProcessing: {os.path.basename(file_path)}")
        print("-" * 40)
        
        if clean_slot_type_file(file_path):
            success_count += 1
            print(f"✅ {os.path.basename(file_path)} cleaned successfully!")
        else:
            print(f"❌ Failed to clean {os.path.basename(file_path)}")
    
    print("=" * 60)
    print(f"Completed: {success_count}/{len(file_paths)} files processed successfully!")

if __name__ == "__main__":
    main()