#!/usr/bin/env python3
"""
Generate Amazon Lex utterances for Chinese restaurant menu ordering.
This script creates comprehensive utterances to maximize recognition accuracy.
"""

import json
import re
import sys
from typing import List, Dict, Any, Set

class LexUtteranceGenerator:
    def __init__(self, menu_file: str):
        """Initialize with menu data file."""
        with open(menu_file, 'r', encoding='utf-8') as f:
            self.menu_data = json.load(f)
        
        # Ordering patterns
        self.base_patterns = [
            "I want {dish}",
            "I'd like {dish}",
            "I'll have {dish}",
            "Can I get {dish}",
            "Give me {dish}",
            "I'll take {dish}",
            "{dish}",
            "I need {dish}",
            "Let me get {dish}",
            "Can I have {dish}",
            "I want the {dish}",
            "I'd like the {dish}",
            "I'll have the {dish}",
            "Can I get the {dish}",
            "Give me the {dish}",
            "I'll take the {dish}",
            "Can I have the {dish}",
            "I want to order {dish}",
            "I'd like to order {dish}",
            "I want an order of {dish}",
            "I'd like an order of {dish}",
            "One order of {dish}",
            "An order of {dish}"
        ]
        
        # Quantity patterns
        self.quantity_patterns = [
            "I want {quantity} {dish}",
            "I'd like {quantity} {dish}",
            "I'll have {quantity} {dish}",
            "Can I get {quantity} {dish}",
            "Give me {quantity} {dish}",
            "I'll take {quantity} {dish}",
            "I need {quantity} {dish}",
            "Let me get {quantity} {dish}",
            "Can I have {quantity} {dish}",
            "I want {quantity} orders of {dish}",
            "I'd like {quantity} orders of {dish}",
            "{quantity} orders of {dish}",
            "{quantity} {dish}",
            "We need {quantity} {dish}",
            "We'll have {quantity} {dish}",
            "We want {quantity} {dish}"
        ]
        
        # Common quantities
        self.quantities = [
            "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            "a", "an"
        ]
        
        # Spice levels
        self.spice_levels = ["mild", "medium", "hot", "spicy", "extra spicy", "extra hot", "not spicy"]
        
        # Common customizations
        self.customizations = [
            "no MSG", "extra sauce", "on the side", "extra spicy", "not spicy",
            "well done", "medium", "extra vegetables", "less salt", "no onions"
        ]
        
    def generate_dish_variations(self, dish_name: str) -> List[str]:
        """Generate variations of dish names including common abbreviations."""
        variations = [dish_name]
        
        # Common abbreviations and variations
        abbreviations = {
            "General Tso's Chicken": ["General Tso", "General Tso's", "GT Chicken", "General Tao"],
            "Sweet & Sour": ["Sweet and Sour", "Sweet Sour"],
            "Black Bean Sauce": ["Black Bean", "Bean Sauce"],
            "Kung Pao": ["Gong Bao", "Kong Pao"],
            "Chow Mein": ["Chow Main", "Lo Mein"],
            "Fried Rice": ["Rice"],
            "Wonton": ["Won Ton"],
            "Barbecued Pork": ["BBQ Pork", "Char Siu", "Cha Siu"],
            "Bean Cake": ["Tofu"],
            "Spareribs": ["Spare Ribs", "Ribs"],
            "Mixed Vegetables": ["Mixed Veggies", "Vegetables"],
            "Broccoli": ["Broccli"],
            "Cashew": ["Cashews"],
            "Almond": ["Almonds"],
            "Double Mushroom": ["Double Mushrooms", "Mushrooms"],
            "Snow Peas": ["Snow Pea"],
            "Seafood": ["Sea Food"],
            "Eggplant": ["Egg Plant"]
        }
        
        # Add common abbreviations
        for full_name, abbrevs in abbreviations.items():
            if full_name.lower() in dish_name.lower():
                for abbrev in abbrevs:
                    variations.append(dish_name.replace(full_name, abbrev))
        
        # Remove duplicates
        return list(set(variations))
    
    def extract_dishes(self) -> List[Dict[str, Any]]:
        """Extract all dishes from menu data."""
        dishes = []
        
        # Extract from menu sections
        for section_name, section_data in self.menu_data["menu_sections"].items():
            if section_name == "family_dinner":
                # Handle family dinner specially
                for style, style_data in section_data.items():
                    if isinstance(style_data, dict) and "includes" in style_data:
                        dish_name = f"{style.replace('_', ' ').title()} Family Dinner"
                        dishes.append({
                            "id": f"family_{style}",
                            "name_en": dish_name,
                            "name_zh": "",
                            "section": section_name,
                            "variations": self.generate_dish_variations(dish_name)
                        })
                        
                        # Add individual items from family dinner
                        for item in style_data["includes"]:
                            if not item.startswith("For"):
                                dishes.append({
                                    "id": f"family_{style}_{len(dishes)}",
                                    "name_en": item,
                                    "name_zh": "",
                                    "section": section_name,
                                    "variations": self.generate_dish_variations(item)
                                })
            elif isinstance(section_data, list):
                # Handle regular menu sections
                for item in section_data:
                    if isinstance(item, dict) and "name_en" in item:
                        variations = self.generate_dish_variations(item["name_en"])
                        dishes.append({
                            "id": item.get("id", f"{section_name}_{len(dishes)}"),
                            "name_en": item["name_en"],
                            "name_zh": item.get("name_zh", ""),
                            "section": section_name,
                            "variations": variations
                        })
        
        return dishes
    
    def create_dish_slot_values(self, dishes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create dish slot values with synonyms for Amazon Lex."""
        slot_values = []
        
        for dish in dishes:
            # Create main slot value
            slot_value = {
                "value": dish["name_en"],
                "synonyms": []
            }
            
            # Add variations as synonyms
            for variation in dish["variations"]:
                if variation != dish["name_en"]:
                    slot_value["synonyms"].append(variation)
            
            # Add Chinese name if available
            if dish["name_zh"]:
                slot_value["synonyms"].append(dish["name_zh"])
            
            # Add dish ID for number ordering
            slot_value["synonyms"].append(str(dish["id"]))
            slot_value["synonyms"].append(f"number {dish['id']}")
            slot_value["synonyms"].append(f"#{dish['id']}")
            
            # Remove duplicates
            slot_value["synonyms"] = list(set(slot_value["synonyms"]))
            
            slot_values.append(slot_value)
        
        return slot_values
    
    def generate_utterances(self, dishes: List[Dict[str, Any]]) -> List[str]:
        """Generate comprehensive utterances for ordering."""
        utterances = set()
        
        # Generate basic ordering utterances with placeholders
        # Basic patterns
        for pattern in self.base_patterns:
            # Replace dish placeholder
            utterances.add(pattern.replace("{dish}", "{DishName}"))
        
        # Quantity patterns
        for pattern in self.quantity_patterns:
            # Replace both quantity and dish placeholders
            utterances.add(pattern.replace("{quantity}", "{Quantity}").replace("{dish}", "{DishName}"))
        
        # With customizations
        customization_patterns = [
            "I want {DishName} {Customization}",
            "I'd like {DishName} {Customization}",
            "{DishName} {Customization}"
        ]
        for pattern in customization_patterns:
            utterances.add(pattern)
        
        # Number ordering patterns
        number_patterns = [
            "I want number {Quantity}",
            "I'd like number {Quantity}",
            "Can I get number {Quantity}",
            "Number {Quantity}",
            "I'll have #{Quantity}"
        ]
        for pattern in number_patterns:
            utterances.add(pattern)
        
        # Combined patterns with quantity and customization
        combined_patterns = [
            "I want {Quantity} {DishName} {Customization}",
            "I'd like {Quantity} {DishName} {Customization}",
            "{Quantity} {DishName} {Customization}",
            "Can I get {Quantity} {DishName} {Customization}",
            "Give me {Quantity} {DishName} {Customization}"
        ]
        for pattern in combined_patterns:
            utterances.add(pattern)
        
        # Specific serving options
        serving_patterns = [
            "{DishName} on Rice",
            "{DishName} Pan Fried Noodles", 
            "{DishName} Chow Fun",
            "I want {DishName} on Rice",
            "I'd like {DishName} on Rice",
            "I'll have {DishName} on Rice",
            "Can I get {DishName} on Rice",
            "Give me {DishName} on Rice",
            "I want {Quantity} {DishName} on Rice",
            "I'd like {Quantity} {DishName} on Rice",
            "I'll have {Quantity} {DishName} on Rice",
            "Can I get {Quantity} {DishName} on Rice",
            "Give me {Quantity} {DishName} on Rice",
            "I want {DishName} Pan Fried Noodles",
            "I'd like {DishName} Pan Fried Noodles",
            "I'll have {DishName} Pan Fried Noodles",
            "Can I get {DishName} Pan Fried Noodles",
            "Give me {DishName} Pan Fried Noodles",
            "I want {Quantity} {DishName} Pan Fried Noodles",
            "I'd like {Quantity} {DishName} Pan Fried Noodles",
            "I'll have {Quantity} {DishName} Pan Fried Noodles",
            "Can I get {Quantity} {DishName} Pan Fried Noodles",
            "Give me {Quantity} {DishName} Pan Fried Noodles",
            "I want {DishName} Chow Fun",
            "I'd like {DishName} Chow Fun",
            "I'll have {DishName} Chow Fun",
            "Can I get {DishName} Chow Fun",
            "Give me {DishName} Chow Fun",
            "I want {Quantity} {DishName} Chow Fun",
            "I'd like {Quantity} {DishName} Chow Fun",
            "I'll have {Quantity} {DishName} Chow Fun",
            "Can I get {Quantity} {DishName} Chow Fun",
            "Give me {Quantity} {DishName} Chow Fun"
        ]
        for pattern in serving_patterns:
            utterances.add(pattern)
        
        # Remove duplicates and return
        return list(set(utterances))
    
    def create_lex_v2_intent(self, dishes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create Amazon Lex V2 intent configuration (clean for AWS CLI)."""
        utterances = self.generate_utterances(dishes)
        # Validate utterances before using them
        utterances = self.validate_utterances(utterances)
        
        intent = {
            "intentName": "OrderFood",
            "description": "Intent for ordering food from Chinese restaurant menu",
            "sampleUtterances": [
                {"utterance": utterance} for utterance in utterances[:1000]  # Lex V2 limit
            ],
            "intentConfirmationSetting": {
                "promptSpecification": {
                    "messageGroups": [
                        {
                            "message": {
                                "plainTextMessage": {
                                    "value": "So you want {Quantity} {DishName}. Is that correct?"
                                }
                            }
                        }
                    ],
                    "maxRetries": 2,
                    "allowInterrupt": True
                },
                "declinationResponse": {
                    "messageGroups": [
                        {
                            "message": {
                                "plainTextMessage": {
                                    "value": "Okay, let me know what you'd like to order."
                                }
                            }
                        }
                    ],
                    "allowInterrupt": True
                }
            },
            "fulfillmentCodeHook": {
                "enabled": True
            },
            "initialResponseSetting": {
                "initialResponse": {
                    "messageGroups": [
                        {
                            "message": {
                                "plainTextMessage": {
                                    "value": "I'd be happy to help you place your order."
                                }
                            }
                        }
                    ],
                    "allowInterrupt": True
                }
            }
        }
        
        return intent
    
    def create_lex_v2_slots(self) -> List[Dict[str, Any]]:
        """Create Amazon Lex V2 slot definitions for intent."""
        slots = [
            {
                "slotName": "DishName",
                "description": "The name of the dish to order",
                "slotTypeName": "DishType",
                "slotConstraint": "Required",
                "valueElicitationSetting": {
                    "slotConstraint": "Required",
                    "promptSpecification": {
                        "messageGroups": [
                            {
                                "message": {
                                    "plainTextMessage": {
                                        "value": "What would you like to order from our menu?"
                                    }
                                }
                            }
                        ],
                        "maxRetries": 3,
                        "allowInterrupt": True
                    }
                }
            },
            {
                "slotName": "Quantity",
                "description": "The quantity of the dish",
                "slotTypeName": "AMAZON.Number",
                "slotConstraint": "Optional"
            },
            {
                "slotName": "Customization",
                "description": "Special customizations for the dish",
                "slotTypeName": "CustomizationType",
                "slotConstraint": "Optional"
            }
        ]
        return slots
    
    def create_lex_v2_slot_priorities(self) -> List[Dict[str, Any]]:
        """Create Amazon Lex V2 slot priorities for intent."""
        slot_priorities = [
            {
                "priority": 1,
                "slotName": "DishName"
            },
            {
                "priority": 2,
                "slotName": "Quantity"
            },
            {
                "priority": 3,
                "slotName": "Customization"
            }
        ]
        return slot_priorities
    
    def create_lex_v2_slot_types(self, dishes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create Amazon Lex V2 slot type configurations (correct V2 format)."""
        dish_slot_values = self.create_dish_slot_values(dishes)
        
        slot_types = {
            "DishType": {
                "slotTypeName": "DishType",
                "description": "All available dishes from the menu",
                "slotTypeValues": [
                    {
                        "sampleValue": {
                            "value": dish["value"]
                        },
                        "synonyms": [
                            {"value": synonym} for synonym in dish["synonyms"]
                        ] if dish["synonyms"] else []
                    } for dish in dish_slot_values
                ],
                "valueSelectionSetting": {
                    "resolutionStrategy": "TopResolution"
                }
            },
            "CustomizationType": {
                "slotTypeName": "CustomizationType", 
                "description": "Common customizations for dishes",
                "slotTypeValues": [
                    {
                        "sampleValue": {
                            "value": customization
                        }
                    } for customization in self.customizations
                ],
                "valueSelectionSetting": {
                    "resolutionStrategy": "TopResolution"
                }
            }
        }
        
        return slot_types
    
    def validate_utterances(self, utterances: List[str]) -> List[str]:
        """Validate utterances for proper placeholder formatting."""
        validated_utterances = []
        nested_placeholder_pattern = r'\{[^}]*\{[^}]*\}[^}]*\}'
        
        for utterance in utterances:
            # Check for nested placeholders
            if re.search(nested_placeholder_pattern, utterance):
                print(f"Warning: Skipping malformed utterance with nested placeholders: {utterance}")
                continue
            
            # Check for unmatched braces
            open_braces = utterance.count('{')
            close_braces = utterance.count('}')
            if open_braces != close_braces:
                print(f"Warning: Skipping utterance with unmatched braces: {utterance}")
                continue
            
            # Check for valid placeholder names
            placeholders = re.findall(r'\{([^}]+)\}', utterance)
            valid_placeholders = {'DishName', 'Quantity', 'Customization'}
            for placeholder in placeholders:
                if placeholder not in valid_placeholders:
                    print(f"Warning: Unknown placeholder '{placeholder}' in utterance: {utterance}")
            
            validated_utterances.append(utterance)
        
        return validated_utterances
    
    def validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """Validate the generated JSON structure for Amazon Lex V2 compatibility."""
        
        # Check if this is an intent or slot type
        if 'intentName' in data:
            # Validate Lex V2 intent structure
            required_keys = ['intentName', 'description', 'sampleUtterances']
            
            for key in required_keys:
                if key not in data:
                    print(f"Error: Missing required key '{key}' in intent structure")
                    return False
            
            # Validate sample utterances structure
            sample_utterances = data.get('sampleUtterances', [])
            if not isinstance(sample_utterances, list):
                print("Error: sampleUtterances must be a list")
                return False
            
            for i, utterance_obj in enumerate(sample_utterances):
                if not isinstance(utterance_obj, dict) or 'utterance' not in utterance_obj:
                    print(f"Error: Sample utterance {i+1} must be a dict with 'utterance' key")
                    return False
            
            # Validate embedded slots if present
            if 'slots' in data:
                slots = data.get('slots', [])
                if not isinstance(slots, list):
                    print("Error: slots must be a list")
                    return False
                
                for i, slot in enumerate(slots):
                    if not isinstance(slot, dict) or 'slotName' not in slot:
                        print(f"Error: Slot {i+1} must be a dict with 'slotName' key")
                        return False
            
            # Validate embedded slot priorities if present
            if 'slotPriorities' in data:
                slot_priorities = data.get('slotPriorities', [])
                if not isinstance(slot_priorities, list):
                    print("Error: slotPriorities must be a list")
                    return False
                
                for i, priority in enumerate(slot_priorities):
                    if not isinstance(priority, dict) or 'slotName' not in priority or 'priority' not in priority:
                        print(f"Error: Slot priority {i+1} must be a dict with 'slotName' and 'priority' keys")
                        return False
            
            # Intent structure validated
                
        elif 'slotTypeName' in data:
            # Validate Lex V2 slot type structure
            required_keys = ['slotTypeName', 'description', 'slotTypeValues']
            
            for key in required_keys:
                if key not in data:
                    print(f"Error: Missing required key '{key}' in slot type structure")
                    return False
            
            # Validate slot type values structure
            slot_type_values = data.get('slotTypeValues', [])
            if not isinstance(slot_type_values, list):
                print("Error: slotTypeValues must be a list")
                return False
                
        elif isinstance(data, list):
            # This is a slots or slot priorities array - valid structure
            pass
        else:
            print("Error: Unknown JSON structure - not a valid Lex V2 intent, slot type, or slot array")
            return False
        
        return True
    
    def save_json_safely(self, data: Dict[str, Any], output_file: str) -> bool:
        """Safely save JSON with validation."""
        try:
            # Validate structure first
            if not self.validate_json_structure(data):
                return False
            
            # Try to serialize to JSON to catch any encoding issues
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Try to parse it back to ensure it's valid
            json.loads(json_str)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            print(f"✓ JSON successfully saved to {output_file}")
            return True
            
        except json.JSONEncodeError as e:
            print(f"Error: Failed to encode JSON: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Generated invalid JSON: {e}")
            return False
        except Exception as e:
            print(f"Error: Failed to save file: {e}")
            return False

def main():
    """Main function to generate Lex V2 utterances and configurations."""
    generator = LexUtteranceGenerator("data/CnRes001/extracted_menu_data.json")
    
    # Extract dishes
    dishes = generator.extract_dishes()
    print(f"Extracted {len(dishes)} dishes from menu")
    
    # Generate Lex V2 intent (clean for AWS CLI)
    intent = generator.create_lex_v2_intent(dishes)
    
    # Generate Lex V2 slots and slot priorities (for separate creation)
    slots = generator.create_lex_v2_slots()
    slot_priorities = generator.create_lex_v2_slot_priorities()
    
    # Generate Lex V2 slot types
    slot_types = generator.create_lex_v2_slot_types(dishes)
    
    # Save intent file
    intent_output_file = "scripts/OrderFood_intent.json"
    if not generator.save_json_safely(intent, intent_output_file):
        print("❌ Failed to save intent JSON file due to validation errors")
        sys.exit(1)
    
    # Save slots file
    slots_output_file = "scripts/OrderFood_slots.json"
    if not generator.save_json_safely(slots, slots_output_file):
        print("❌ Failed to save slots JSON file due to validation errors")
        sys.exit(1)
    
    # Save slot priorities file
    slot_priorities_output_file = "scripts/OrderFood_slot_priorities.json"
    if not generator.save_json_safely(slot_priorities, slot_priorities_output_file):
        print("❌ Failed to save slot priorities JSON file due to validation errors")
        sys.exit(1)
    
    # Save slot type files
    for slot_type_name, slot_type_config in slot_types.items():
        slot_type_output_file = f"scripts/{slot_type_name}.json"
        if not generator.save_json_safely(slot_type_config, slot_type_output_file):
            print(f"❌ Failed to save slot type JSON file {slot_type_output_file} due to validation errors")
            sys.exit(1)
    
    print(f"Generated {len(intent['sampleUtterances'])} utterances")
    print(f"Created {len(slot_types['DishType']['slotTypeValues'])} dish slot values")
    print(f"Created {len(slot_types['CustomizationType']['slotTypeValues'])} customization slot values")
    
    # Final validation check for all files
    all_files = [intent_output_file, slots_output_file, slot_priorities_output_file] + [f"scripts/{name}.json" for name in slot_types.keys()]
    
    for file_path in all_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"✅ Final validation: {file_path} is valid and ready for use")
        except Exception as e:
            print(f"❌ Final validation failed for {file_path}: {e}")
            sys.exit(1)
    
    # Print some sample utterances
    print(f"\nGenerated files for Lex V2:")
    print(f"1. Intent: {intent_output_file}")
    print(f"2. Slots: {slots_output_file}")
    print(f"3. Slot Priorities: {slot_priorities_output_file}")
    for i, (slot_type_name, _) in enumerate(slot_types.items(), 4):
        print(f"{i}. Slot Type: scripts/{slot_type_name}.json")
    
    print(f"\nSample utterances:")
    for i, utterance in enumerate(intent['sampleUtterances'][:10]):
        print(f"{i+1}. {utterance['utterance']}")
    
    print(f"\nTo use with AWS CLI Lex V2:")
    print(f"# Step 1: Create slot types first (order matters!):")
    for slot_type_name in slot_types.keys():
        print(f"aws lexv2-models create-slot-type --bot-id <BOT_ID> --bot-version DRAFT --locale-id en_US --cli-input-json file://scripts/{slot_type_name}.json")
    print(f"\n# Step 2: Create the intent:")
    print(f"aws lexv2-models create-intent --bot-id <BOT_ID> --bot-version DRAFT --locale-id en_US --cli-input-json file://{intent_output_file}")
    print(f"\n# Step 3: Add slots to the intent (repeat for each slot):")
    for slot in slots:
        slot_name = slot['slotName']
        print(f"aws lexv2-models create-slot --bot-id <BOT_ID> --bot-version DRAFT --locale-id en_US --intent-id <INTENT_ID> --slot-name {slot_name} --slot-type-name {slot['slotTypeName']} --slot-constraint {slot['slotConstraint']}")
    print(f"\nNote: Replace <BOT_ID> and <INTENT_ID> with actual values from previous commands")

if __name__ == "__main__":
    main()