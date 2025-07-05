#!/bin/bash

echo "🚀 Simple AWS Lex Bot Check"
echo "=================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   brew install awscli  # for macOS"
    echo "   pip install awscli   # for other systems"
    exit 1
fi

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    echo ""
    echo "You'll need:"
    echo "   - AWS Access Key ID"
    echo "   - AWS Secret Access Key"
    echo "   - Default region name (e.g., us-east-1, us-west-2)"
    echo "   - Default output format (json)"
    exit 1
fi

echo "✅ AWS credentials configured"

# Check current region
REGION=$(aws configure get region)
echo "🌍 Current AWS region: ${REGION:-default}"

if [ -z "$REGION" ]; then
    echo "⚠️  No default region set. Consider setting one with:"
    echo "   aws configure set region us-east-1"
fi

echo ""
echo "🔍 Checking for Amazon Lex V2 Bots..."
echo "=================================================="

# List Lex V2 bots (without jq)
echo "📋 Attempting to list Lex V2 bots..."
BOTS_RESULT=$(aws lexv2-models list-bots 2>&1)
BOTS_EXIT_CODE=$?

if [ $BOTS_EXIT_CODE -eq 0 ]; then
    echo "✅ Successfully connected to Lex V2 service"
    echo "Raw response:"
    echo "$BOTS_RESULT"
    
    # Check if there are bots
    if echo "$BOTS_RESULT" | grep -q '"botSummaries": \[\]'; then
        echo ""
        echo "📭 No bots found in Lex V2"
        echo "You need to create a bot first!"
    elif echo "$BOTS_RESULT" | grep -q '"botSummaries"'; then
        echo ""
        echo "🎉 Found some bots! Check the response above for details."
    fi
else
    echo "❌ Error accessing Lex V2:"
    echo "$BOTS_RESULT"
fi

echo ""
echo "🔍 Checking for Amazon Lex V1 (Legacy)..."
echo "=================================================="

# Check Lex V1 intents
echo "📝 Attempting to list Lex V1 intents..."
V1_INTENTS_RESULT=$(aws lex-models get-intents 2>&1)
V1_INTENTS_EXIT_CODE=$?

if [ $V1_INTENTS_EXIT_CODE -eq 0 ]; then
    echo "✅ Successfully connected to Lex V1 service"
    echo "Raw response:"
    echo "$V1_INTENTS_RESULT"
else
    echo "❌ Error accessing Lex V1:"
    echo "$V1_INTENTS_RESULT"
fi

echo ""
echo "🔍 Checking for slot types..."
V1_SLOTS_RESULT=$(aws lex-models get-slot-types 2>&1)
V1_SLOTS_EXIT_CODE=$?

if [ $V1_SLOTS_EXIT_CODE -eq 0 ]; then
    echo "✅ Slot types response:"
    echo "$V1_SLOTS_RESULT"
else
    echo "❌ Error accessing slot types:"
    echo "$V1_SLOTS_RESULT"
fi

echo ""
echo "🛠️ Next Steps"
echo "=================================================="

if [ $BOTS_EXIT_CODE -ne 0 ] && [ $V1_INTENTS_EXIT_CODE -ne 0 ]; then
    echo "❌ No access to Lex services. Please check:"
    echo ""
    echo "1. 🔑 IAM Permissions - Your AWS user/role needs:"
    echo "   - lex:* (for Lex V1)"
    echo "   - lexv2:* (for Lex V2)"
    echo ""
    echo "2. 🌍 Region - Lex may not be available in your current region"
    echo "   Try switching to a supported region like:"
    echo "   aws configure set region us-east-1"
    echo "   aws configure set region us-west-2"
    echo ""
    echo "3. 📋 Service availability - Check if Lex is available in your region:"
    echo "   https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/"
    
elif echo "$BOTS_RESULT" | grep -q '"botSummaries": \[\]' && echo "$V1_INTENTS_RESULT" | grep -q '"intents": \[\]'; then
    echo "✅ You have access to Lex, but no bots/intents exist yet."
    echo ""
    echo "🚀 To get started:"
    echo ""
    echo "1. Create a bot in the AWS Console:"
    echo "   https://console.aws.amazon.com/lexv2/"
    echo ""
    echo "2. Or create a slot type first using your JSON file:"
    echo "   aws lexv2-models create-slot-type --help"
    echo ""
    echo "3. Then create intents that use your slot types"
    echo ""
    echo "4. Re-run this script to get the IDs for your AWS CLI commands"
    
else
    echo "🎉 You have Lex resources! Check the responses above for:"
    echo ""
    echo "- Bot IDs (botId)"
    echo "- Intent IDs (intentId)" 
    echo "- Slot Type IDs (slotTypeId)"
    echo ""
    echo "💡 Tip: Install 'jq' for better JSON parsing:"
    echo "   brew install jq  # for macOS"
    echo ""
    echo "Then you can extract IDs like:"
    echo "   aws lexv2-models list-bots | jq -r '.botSummaries[0].botId'"
fi

echo ""
echo "=================================================="