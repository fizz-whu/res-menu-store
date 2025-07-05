#!/usr/bin/env python3
"""
Script to clean up CnRes001_slot_type_CustomizationType_v2.json file:
1. If any synonym value contains '_' or a number, make synonyms an empty list
2. Replace all 'w/' with 'with' in all values and synonyms
"""

import json
import re
import os

def contains_underscore_or_number(text):
    """Check if text contains underscore or any digit"""
    return '_' in text or any(char.isdigit() for char in text)

def replace_w_with_with(text):
    """Replace 'w/' with 'with' in text"""
    return text.replace('w/', 'with')

def clean_customization_file(file_path):
    """Clean the customization type JSON file"""
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False
    
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Processing file: {file_path}")
        modifications_made = 0
        
        # Process each slot type value
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
                # Check if any synonym contains underscore or number
                should_clear_synonyms = False
                
                for synonym in slot_value['synonyms']:
                    if 'value' in synonym:
                        synonym_value = synonym['value']
                        if contains_underscore_or_number(synonym_value):
                            should_clear_synonyms = True
                            print(f"Found problematic synonym '{synonym_value}' - will clear all synonyms for this slot")
                            break
                
                if should_clear_synonyms:
                    # Clear all synonyms for this slot value
                    slot_value['synonyms'] = []
                    modifications_made += 1
                    print(f"Cleared synonyms for slot value: {slot_value['sampleValue']['value']}")
                else:
                    # Replace w/ with with in all synonyms
                    for synonym in slot_value['synonyms']:
                        if 'value' in synonym:
                            original_synonym = synonym['value']
                            new_synonym = replace_w_with_with(original_synonym)
                            if new_synonym != original_synonym:
                                synonym['value'] = new_synonym
                                print(f"Updated synonym: '{original_synonym}' -> '{new_synonym}'")
                                modifications_made += 1
        
        # Write the modified data back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nProcessing complete!")
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
    # File path
    file_path = "/Users/fizz/work/res-menu-store/scripts/CnRes001_slot_type_CustomizationType_v2.json"
    
    print("Starting cleanup of CustomizationType file...")
    print("=" * 60)
    
    success = clean_customization_file(file_path)
    
    if success:
        print("=" * 60)
        print("✅ File cleanup completed successfully!")
    else:
        print("=" * 60)
        print("❌ File cleanup failed!")

if __name__ == "__main__":
    main()