#!/usr/bin/env python3
"""
Script to verify that all dishes in the JSON file have populated synonyms arrays.
"""

import json
import sys
from pathlib import Path

def verify_synonyms(json_file_path):
    """
    Verify that no dish has an empty synonyms array.
    
    Args:
        json_file_path (str): Path to the JSON file
    
    Returns:
        tuple: (bool, list) - (all_populated, empty_dishes_list)
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {json_file_path}")
        return False, []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format: {e}")
        return False, []
    
    # Check if the expected structure exists
    if 'slotTypeValues' not in data:
        print("❌ Error: 'slotTypeValues' key not found in JSON")
        return False, []
    
    slot_type_values = data['slotTypeValues']
    empty_dishes = []
    total_dishes = len(slot_type_values)
    
    print(f"🔍 Analyzing {total_dishes} dishes...")
    print("=" * 50)
    
    for i, dish in enumerate(slot_type_values):
        # Check if required keys exist
        if 'sampleValue' not in dish or 'value' not in dish['sampleValue']:
            print(f"⚠️  Warning: Dish at index {i} missing sampleValue.value")
            continue
            
        dish_name = dish['sampleValue']['value']
        
        # Check if synonyms key exists
        if 'synonyms' not in dish:
            empty_dishes.append({
                'index': i,
                'name': dish_name,
                'issue': 'Missing synonyms key'
            })
            continue
        
        synonyms = dish['synonyms']
        
        # Check if synonyms is empty
        if not synonyms or len(synonyms) == 0:
            empty_dishes.append({
                'index': i,
                'name': dish_name,
                'issue': 'Empty synonyms array'
            })
        else:
            # Additional check: ensure synonyms have proper structure
            for j, synonym in enumerate(synonyms):
                if not isinstance(synonym, dict) or 'value' not in synonym:
                    empty_dishes.append({
                        'index': i,
                        'name': dish_name,
                        'issue': f'Invalid synonym structure at synonym index {j}'
                    })
                    break
    
    return len(empty_dishes) == 0, empty_dishes

def print_results(all_populated, empty_dishes, total_count):
    """Print the verification results."""
    print("\n" + "=" * 50)
    print("📋 VERIFICATION RESULTS")
    print("=" * 50)
    
    if all_populated:
        print("✅ SUCCESS: All dishes have populated synonyms!")
        print(f"📊 Total dishes verified: {total_count}")
        print("🎉 The JSON file is ready for use!")
    else:
        print("❌ ISSUES FOUND: Some dishes have empty or invalid synonyms")
        print(f"📊 Total dishes: {total_count}")
        print(f"🚨 Dishes with issues: {len(empty_dishes)}")
        print("\n📝 List of dishes with empty/invalid synonyms:")
        print("-" * 40)
        
        for dish in empty_dishes:
            print(f"Index {dish['index']:3d}: {dish['name']}")
            print(f"             Issue: {dish['issue']}")
            print()

def main():
    """Main execution function."""
    json_file_path = "/Users/fizz/work/res-menu-store/scripts/CnRes001_slot_type_DishType_v2.json"
    
    print("🔍 Synonym Verification Tool")
    print("=" * 50)
    print(f"📁 File: {json_file_path}")
    
    # Check if file exists
    if not Path(json_file_path).exists():
        print(f"❌ Error: File does not exist: {json_file_path}")
        sys.exit(1)
    
    # Verify synonyms
    all_populated, empty_dishes = verify_synonyms(json_file_path)
    
    # Load data to get total count
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    total_count = len(data.get('slotTypeValues', []))
    
    # Print results
    print_results(all_populated, empty_dishes, total_count)
    
    # Exit with appropriate code
    sys.exit(0 if all_populated else 1)

if __name__ == "__main__":
    main()