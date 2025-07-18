# Lambda Function Usage Display Example

When you run the tool, you'll see a detailed summary of Lambda function usage like this:

```
============================================================
LAMBDA FUNCTION USAGE SUMMARY
============================================================

🔗 DIRECTLY CONNECTED FUNCTIONS (2):
These functions are actively used by the bot
------------------------------------------------------------

📋 Function: OrderProcessorFunction
   Runtime: python3.9
   Handler: lambda_function.lambda_handler
   Description: Processes customer orders for the restaurant
   Used in 2 location(s):
     🎯 Intent: OrderIntent (fulfillment)
        Purpose: Handles intent fulfillment (final action)
        Locale: en_US
     💬 Intent: OrderIntent (dialog)
        Purpose: Handles dialog management (slot validation, etc.)
        Locale: en_US

📋 Function: MenuQueryFunction
   Runtime: python3.9
   Handler: index.handler
   Description: Queries menu information and availability
   Used in 1 location(s):
     🎯 Intent: MenuInquiryIntent (fulfillment)
        Purpose: Handles intent fulfillment (final action)
        Locale: en_US

🔍 POTENTIALLY RELATED FUNCTIONS (1):
These functions were found by name/description matching
------------------------------------------------------------

📋 Function: RestaurantLexBot
   Runtime: nodejs18.x
   Handler: index.handler
   Description: General bot utility functions
   🔍 Potentially related (name/description match)

============================================================
HOOK TYPE EXPLANATIONS:
🎯 Fulfillment: Handles the final action after all slots are filled
💬 Dialog: Manages conversation flow and slot validation
============================================================
```

## What This Tells You

### 🔗 Directly Connected Functions
- These functions are actually configured in your bot's intents
- You can see exactly which intents use them and for what purpose
- These are the functions you'll most likely want to modify
- **Only these functions are shown by default**

### 🔍 Potentially Related Functions
- These functions were found by name/description matching
- They might be related to your bot but aren't directly connected
- Review these to see if they should be connected to intents
- **Only shown when using `--include-fallback`**

### Default vs Fallback Mode

**Default mode (no flags):**
```bash
python lex_bot_manager.py
```
- Shows only directly connected Lambda functions
- Guarantees that all listed functions are actually used by the bot
- Cleaner output, focused on actual usage

**Fallback mode:**
```bash
python lex_bot_manager.py --include-fallback
```
- Shows both directly connected AND potentially related functions
- Helps find functions that might be related but not connected
- More comprehensive but potentially includes unrelated functions

### Hook Types
- **Fulfillment (🎯)**: Runs after all required slots are filled, handles the final action
- **Dialog (💬)**: Runs during the conversation to validate slots and manage flow

## Component Selection Menu

When selecting components, Lambda functions show their usage inline:

```
Available Components:
--------------------------------------------------
1. [INTENTS] OrderIntent (Locale: en_US)
2. [INTENTS] MenuInquiryIntent (Locale: en_US)
3. [SLOTS] MenuCategory (Locale: en_US)
4. [LAMBDA_FUNCTIONS] OrderProcessorFunction (DIRECT)
    Used in:
      - Intent: OrderIntent (fulfillment) - Handles intent fulfillment (final action) [Locale: en_US]
      - Intent: OrderIntent (dialog) - Handles dialog management (slot validation, etc.) [Locale: en_US]
5. [LAMBDA_FUNCTIONS] MenuQueryFunction (DIRECT)
    Used in:
      - Intent: MenuInquiryIntent (fulfillment) - Handles intent fulfillment (final action) [Locale: en_US]
6. [LAMBDA_FUNCTIONS] RestaurantLexBot (INFERRED)
    Usage: Potentially related (name/description match)
7. Exit
```

This makes it easy to identify which Lambda function you need to modify for specific functionality!