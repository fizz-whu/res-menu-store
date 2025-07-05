#!/usr/bin/env python3
import json
import re

def fix_placeholders(text):
    """Fix malformed placeholders in utterances."""
    if not isinstance(text, str):
        return text
    
    # Fix nested placeholders like {DishN{Quantity}me} -> {DishName}
    text = re.sub(r'\{DishN\{Quantity\}me\}', '{DishName}', text)
    
    # Fix malformed placeholders where {Quantity} is inserted into words
    # h{Quantity}ve -> have
    text = re.sub(r'h\{Quantity\}ve', 'have', text)
    
    # w{Quantity}nt -> want
    text = re.sub(r'w\{Quantity\}nt', 'want', text)
    
    # C{Quantity}n -> Can
    text = re.sub(r'C\{Quantity\}n', 'Can', text)
    
    # t{Quantity}ke -> take
    text = re.sub(r't\{Quantity\}ke', 'take', text)
    
    # extr{Quantity} -> extra
    text = re.sub(r'extr\{Quantity\}', 'extra', text)
    
    # veget{Quantity}bles -> vegetables
    text = re.sub(r'veget\{Quantity\}bles', 'vegetables', text)
    
    # s{Quantity}uce -> sauce
    text = re.sub(r's\{Quantity\}uce', 'sauce', text)
    
    # s{Quantity}lt -> salt
    text = re.sub(r's\{Quantity\}lt', 'salt', text)
    
    # P{Quantity}n -> Pan
    text = re.sub(r'P\{Quantity\}n', 'Pan', text)
    
    # #{Quantity}8 -> {Quantity}
    text = re.sub(r'#\{Quantity\}8', '{Quantity}', text)
    
    # {Quantity}n -> {Quantity}
    text = re.sub(r'\{Quantity\}n', '{Quantity}', text)
    
    return text

def fix_json_file(input_file, output_file):
    """Fix all malformed placeholders in the JSON file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Fix utterances in the data
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'utterance' in item:
                item['utterance'] = fix_placeholders(item['utterance'])
    elif isinstance(data, dict):
        for key, value in data.items():
            if key == 'utterance':
                data[key] = fix_placeholders(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and 'utterance' in item:
                        item['utterance'] = fix_placeholders(item['utterance'])
    
    # Write the fixed data back to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    input_file = '/Users/fizz/work/res-menu-store/scripts/CnRes001_intent_order_0.json'
    output_file = '/Users/fizz/work/res-menu-store/scripts/CnRes001_intent_order_0.json'
    
    fix_json_file(input_file, output_file)
    print("JSON file has been fixed!")