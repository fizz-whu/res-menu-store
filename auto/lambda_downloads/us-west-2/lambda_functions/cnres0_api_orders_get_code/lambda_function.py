import json
import boto3
from decimal import Decimal

# Custom JSON encoder to handle Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimal to float or int, depending on your use case
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    # DynamoDB table name
    table_name = "cnres0_orders"  # Replace with your DynamoDB table name
    
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    print(f"Fetching all records from table: {table_name}")
    
    # Scan DynamoDB
    try:
        # Initialize an empty list to hold all items
        all_items = []
        
        # Perform the initial scan
        response = table.scan()
        all_items.extend(response.get('Items', []))
        
        # Handle pagination if there are more items to fetch
        while 'LastEvaluatedKey' in response:
            print("Fetching next page of results...")
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            all_items.extend(response.get('Items', []))
        
        print('Total records fetched:', len(all_items))
        
        # Return the items using the custom encoder
        return {
            "statusCode": 200,
            "body": json.dumps(all_items, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error scanning DynamoDB table: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
