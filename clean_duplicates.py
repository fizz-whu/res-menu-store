#!/usr/bin/env python3
"""
Script to remove duplicate slot values from DishType.json
"""

import json
from typing import Dict, List, Any

def clean_duplicates(file_path: str, output_path: str = None) -> None:
    """Remove duplicate slot values from DishType slot type"""
    
    if output_path is None:
        output_path = file_path
    
    # Load the JSON data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Track seen values to identify duplicates
    seen_values = set()
    cleaned_values = []
    duplicates_found = []
    
    for slot_value in data['slotTypeValues']:
        sample_value = slot_value['sampleValue']['value']
        
        if sample_value.lower() not in seen_values:
            seen_values.add(sample_value.lower())
            cleaned_values.append(slot_value)
        else:
            duplicates_found.append(sample_value)
            print(f"Removing duplicate: {sample_value}")
    
    # Update the data with cleaned values
    data['slotTypeValues'] = cleaned_values
    
    # Save the cleaned data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nCleaning complete!")
    print(f"Original count: {len(data['slotTypeValues']) + len(duplicates_found)}")
    print(f"Cleaned count: {len(cleaned_values)}")
    print(f"Duplicates removed: {len(duplicates_found)}")
    
    if duplicates_found:
        print("\nDuplicates found and removed:")
        for dup in duplicates_found:
            print(f"  - {dup}")

def main():
    # Clean the DishType.json file
    print("Cleaning duplicates from DishType.json...")
    clean_duplicates('scripts/DishType.json')
    
    # Also clean the v2 file if it exists
    try:
        print("\nCleaning duplicates from CnRes001_slot_type_DishType_v2.json...")
        clean_duplicates('scripts/CnRes001_slot_type_DishType_v2.json')
    except FileNotFoundError:
        print("CnRes001_slot_type_DishType_v2.json not found, skipping...")

if __name__ == "__main__":
    main()