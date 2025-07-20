#!/bin/bash
# Deploy script for the updated lambda function

echo "🚀 Deploying Updated Lambda Function with Pricing Features"
echo "=========================================================="

# Configuration
FUNCTION_NAME="test_dynamo_write_0"  # Your existing Lambda function
REGION="us-west-2"

# Check if function name is provided
if [ "$FUNCTION_NAME" = "your-lambda-function-name" ]; then
    echo "❌ Please update FUNCTION_NAME in this script with your actual Lambda function name"
    exit 1
fi

echo "📦 Creating deployment package..."

# Create deployment package
zip -r lambda-deployment.zip lambda_function.py

echo "📤 Uploading to Lambda function: $FUNCTION_NAME"

# Update Lambda function code
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://lambda-deployment.zip \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Lambda function updated successfully!"
    echo "🔧 Updating environment variables..."
    
    # Update environment variables if needed
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --environment Variables="{MENU_TABLE=RestaurantMenuOptimized,ORDERS_TABLE=cnres0_orders}" \
        --region $REGION
    
    echo "✅ Deployment completed successfully!"
    echo "📋 Function details:"
    aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.[FunctionName,Runtime,LastModified,CodeSize]' --output table
else
    echo "❌ Deployment failed. Please check your AWS credentials and function name."
fi

# Cleanup
rm -f lambda-deployment.zip
echo "🧹 Cleanup completed"
