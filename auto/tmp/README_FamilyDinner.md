# Family Dinner Intent Implementation Guide

## Overview
The OrderFamilyDinnerIntent handles family dinner packages that come in two styles:
- **Hong Kong Style**: $14.75 per person
- **Peking Style**: $15.75 per person

Both require a minimum of 2 people and include additional dishes based on party size.

## Files Created

### 1. OrderFamilyDinnerIntent.json
The main intent configuration file that includes:
- Sample utterances for various ways users might order family dinners
- Two required slots: NumberOfPeople and FamilyDinnerStyle
- Confirmation prompt and rejection statement

### 2. FamilyDinnerStyles.json
Custom slot type that defines the two family dinner styles with synonyms:
- Hong Kong style (synonyms: Hong Kong, HK, HK style, hongkong)
- Peking style (synonyms: Peking, Beijing, Beijing style, beijing)

### 3. OrderFamilyDinnerLambda.js
Lambda function that handles the fulfillment logic:
- Validates minimum 2 people requirement
- Calculates total price based on style and number of people
- Determines which dishes are included based on party size
- Returns a formatted response with order details

### 4. FamilyDinnerTestConversations.md
Example conversations showing various test cases

## Menu Structure

### Hong Kong Style ($14.75/person)
**Base dishes (2+ people):**
- Spring Egg Rolls
- Minced Beef with Egg White Soup
- Beef with Broccoli
- Shrimp with Mixed Vegetables
- Barbecued Pork Fried Rice

**Additional dishes:**
- 3+ people: Add Succulent Spicy Pork with Garlic Sauce
- 4+ people: Add Clams with Black Bean Sauce
- 5+ people: Add Braised Fish Fillet
- 6+ people: Add Double Mushroom with Oyster Sauce

### Peking Style ($15.75/person)
**Base dishes (2+ people):**
- Golden Pot Stickers
- Hot & Sour Soup
- Mongolian Beef
- Kung Pao Shrimp
- Yang Chow Fried Rice

**Additional dishes:**
- 3+ people: Add Spicy Hot Bean Curd with Minced Pork
- 4+ people: Add Squids with Green Onion
- 5+ people: Add Sliced Rock Cod with Special Sauce
- 6+ people: Add Snow Pea with Mushroom

## Implementation Steps

1. **Create the custom slot type** in AWS Lex console using FamilyDinnerStyles.json
2. **Create the intent** using OrderFamilyDinnerIntent.json
3. **Deploy the Lambda function** (OrderFamilyDinnerLambda.js) to AWS Lambda
4. **Configure the intent** to use the Lambda function for fulfillment
5. **Test the bot** using the conversations in FamilyDinnerTestConversations.md

## Key Features

- **Flexible utterances**: Supports various ways to order (with/without style specified)
- **Smart validation**: Enforces minimum 2 people requirement
- **Dynamic menu**: Automatically adds dishes based on party size
- **Price calculation**: Calculates total based on style and number of people
- **Session attributes**: Stores order details for potential use in other intents

## Error Handling

The Lambda function handles:
- Invalid number of people (less than 2)
- Missing family dinner style
- Invalid style values

## Future Enhancements

Consider adding:
- Special dietary restrictions handling
- Ability to swap dishes
- Integration with payment processing
- Order modification capabilities
- Delivery time estimates based on party size