#!/bin/bash

echo "🚀 AWS Lex Bot ID Retrieval Tool"
echo "=================================================="

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

CALLER_IDENTITY=$(aws sts get-caller-identity)
echo "✅ AWS credentials configured"
echo "Account: $(echo $CALLER_IDENTITY | jq -r '.Account')"
echo "User/Role: $(echo $CALLER_IDENTITY | jq -r '.Arn')"
echo ""

echo "🔍 Amazon Lex V2 Information"
echo "=================================================="

# List Lex V2 bots
echo "📋 Available Lex V2 Bots:"
echo "--------------------------------------------------"

BOTS_JSON=$(aws lexv2-models list-bots 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "❌ Error accessing Lex V2 or no bots found"
    echo "Make sure you have the correct permissions and region set"
else
    echo "$BOTS_JSON" | jq -r '.botSummaries[] | "Bot Name: \(.botName)\nBot ID: \(.botId)\nStatus: \(.botStatus)\nDescription: \(.description // "N/A")\n"'
    
    # Get the first bot ID for further operations
    BOT_ID=$(echo "$BOTS_JSON" | jq -r '.botSummaries[0].botId')
    BOT_NAME=$(echo "$BOTS_JSON" | jq -r '.botSummaries[0].botName')
    
    if [ "$BOT_ID" != "null" ] && [ "$BOT_ID" != "" ]; then
        echo "🎯 Using Bot: $BOT_NAME (ID: $BOT_ID)"
        echo ""
        
        # Get locales
        echo "🌐 Available Locales:"
        echo "--------------------------------------------------"
        LOCALES_JSON=$(aws lexv2-models list-bot-locales --bot-id "$BOT_ID" --bot-version "DRAFT" 2>/dev/null)
        
        if [ $? -eq 0 ]; then
            echo "$LOCALES_JSON" | jq -r '.botLocaleSummaries[] | "Locale: \(.localeId) (\(.localeName))"'
            
            # Get the first locale
            LOCALE_ID=$(echo "$LOCALES_JSON" | jq -r '.botLocaleSummaries[0].localeId')
            echo "🎯 Using Locale: $LOCALE_ID"
            echo ""
            
            # Get intents
            echo "📝 Available Intents:"
            echo "--------------------------------------------------"
            INTENTS_JSON=$(aws lexv2-models list-intents --bot-id "$BOT_ID" --bot-version "DRAFT" --locale-id "$LOCALE_ID" 2>/dev/null)
            
            if [ $? -eq 0 ]; then
                echo "$INTENTS_JSON" | jq -r '.intentSummaries[] | "Intent Name: \(.intentName)\nIntent ID: \(.intentId)\nDescription: \(.description // "N/A")\n"'
                
                # Get first intent ID
                INTENT_ID=$(echo "$INTENTS_JSON" | jq -r '.intentSummaries[0].intentId')
                INTENT_NAME=$(echo "$INTENTS_JSON" | jq -r '.intentSummaries[0].intentName')
            else
                echo "❌ No intents found or error accessing intents"
            fi
            
            # Get slot types
            echo "🎰 Available Slot Types:"
            echo "--------------------------------------------------"
            SLOT_TYPES_JSON=$(aws lexv2-models list-slot-types --bot-id "$BOT_ID" --bot-version "DRAFT" --locale-id "$LOCALE_ID" 2>/dev/null)
            
            if [ $? -eq 0 ]; then
                echo "$SLOT_TYPES_JSON" | jq -r '.slotTypeSummaries[] | "Slot Type Name: \(.slotTypeName)\nSlot Type ID: \(.slotTypeId)\nDescription: \(.description // "N/A")\n"'
                
                # Look for DishType slot
                DISH_TYPE_SLOT_ID=$(echo "$SLOT_TYPES_JSON" | jq -r '.slotTypeSummaries[] | select(.slotTypeName == "DishType") | .slotTypeId')
                
                if [ "$DISH_TYPE_SLOT_ID" != "" ] && [ "$DISH_TYPE_SLOT_ID" != "null" ]; then
                    echo "🍽️ Found DishType slot type!"
                    echo "   ID: $DISH_TYPE_SLOT_ID"
                    echo ""
                fi
            else
                echo "❌ No slot types found or error accessing slot types"
            fi
            
        else
            echo "❌ Error accessing locales"
        fi
    fi
fi

echo ""
echo "🔍 Amazon Lex V1 Information (Legacy)"
echo "=================================================="

# List Lex V1 intents
echo "📝 Available Lex V1 Intents:"
echo "--------------------------------------------------"
V1_INTENTS=$(aws lex-models get-intents 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$V1_INTENTS" | jq -r '.intents[] | "Intent Name: \(.name)\nVersion: \(.version)\nDescription: \(.description // "N/A")\n"'
else
    echo "❌ No Lex V1 intents found or error accessing Lex V1"
fi

# List Lex V1 slot types
echo "🎰 Available Lex V1 Slot Types:"
echo "--------------------------------------------------"
V1_SLOT_TYPES=$(aws lex-models get-slot-types 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$V1_SLOT_TYPES" | jq -r '.slotTypes[] | "Slot Type Name: \(.name)\nVersion: \(.version)\nDescription: \(.description // "N/A")\n"'
else
    echo "❌ No Lex V1 slot types found or error accessing Lex V1"
fi

echo ""
echo "🛠️ Generated AWS CLI Commands"
echo "=================================================="

if [ "$BOT_ID" != "" ] && [ "$BOT_ID" != "null" ] && [ "$LOCALE_ID" != "" ] && [ "$INTENT_ID" != "" ]; then
    echo "✅ All required IDs found! Here's your command:"
    echo ""
    echo "📋 Command to update intent:"
    echo "--------------------------------------------------"
    
    cat << EOF
aws lexv2-models update-intent \\
    --bot-id "$BOT_ID" \\
    --bot-version "DRAFT" \\
    --locale-id "$LOCALE_ID" \\
    --intent-id "$INTENT_ID" \\
    --intent-name "$INTENT_NAME" \\
    --description "Updated intent for ordering dishes" \\
    --sample-utterances '[
        {
            "utterance": "I want to order {DishType}"
        },
        {
            "utterance": "Can I get {DishType}"
        },
        {
            "utterance": "I would like {DishType}"
        }
    ]'
EOF

    if [ "$DISH_TYPE_SLOT_ID" != "" ] && [ "$DISH_TYPE_SLOT_ID" != "null" ]; then
        cat << EOF
 \\
    --slots '[
        {
            "slotName": "DishType",
            "description": "Type of dish to order",
            "slotTypeId": "$DISH_TYPE_SLOT_ID",
            "valueElicitationSetting": {
                "slotConstraint": "Required",
                "promptSpecification": {
                    "messageGroups": [
                        {
                            "message": {
                                "plainTextMessage": {
                                    "value": "What dish would you like to order?"
                                }
                            }
                        }
                    ],
                    "maxRetries": 3
                }
            }
        }
    ]'
EOF
    fi
    
    echo ""
    echo ""
    echo "📝 Key Information Summary:"
    echo "--------------------------------------------------"
    echo "Bot ID: $BOT_ID"
    echo "Bot Name: $BOT_NAME"
    echo "Locale ID: $LOCALE_ID"
    echo "Intent ID: $INTENT_ID"
    echo "Intent Name: $INTENT_NAME"
    [ "$DISH_TYPE_SLOT_ID" != "" ] && [ "$DISH_TYPE_SLOT_ID" != "null" ] && echo "DishType Slot ID: $DISH_TYPE_SLOT_ID"
    
    echo ""
    echo "🚀 Next Steps:"
    echo "1. Copy the command above"
    echo "2. Modify the intent details as needed"
    echo "3. Run the command to update your intent"
    echo "4. Build your bot locale with:"
    echo "   aws lexv2-models build-bot-locale --bot-id \"$BOT_ID\" --bot-version \"DRAFT\" --locale-id \"$LOCALE_ID\""
    
else
    echo "❌ Missing required information to generate commands"
    echo "Bot ID: ${BOT_ID:-NOT FOUND}"
    echo "Locale ID: ${LOCALE_ID:-NOT FOUND}"
    echo "Intent ID: ${INTENT_ID:-NOT FOUND}"
    echo ""
    echo "Please check:"
    echo "1. AWS credentials are configured correctly"
    echo "2. You have access to Amazon Lex"
    echo "3. You have at least one bot with intents created"
    echo "4. You're using the correct AWS region"
fi

echo ""
echo "=================================================="