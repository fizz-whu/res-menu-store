import boto3
import json
import datetime

# DynamoDB table name
ORDERS_TABLE = "cnres0_orders"

# SNS endpoint ARN
endpoint_arn = "arn:aws:sns:us-west-2:495599767527:endpoint/APNS_SANDBOX/CnResOrderDisplayNotificationDev/e9792aab-7449-3d7b-98ac-2ebf2ef919fc"

# AWS clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns', region_name='us-west-2')

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))
    
    try:
        # Extract intent and slots
        intent_name = event['sessionState']['intent']['name']
        slots = event['sessionState']['intent']['slots']
        
        # Fixed slot names to match actual Lex event
        dish_name = slots['DishName']['value']['interpretedValue']
        quantity = int(slots['Quantity']['value']['interpretedValue'])
        
        # Handle optional Customization slot
        customization = None
        if slots.get('Customization') and slots['Customization']:
            if isinstance(slots['Customization']['value'], dict):
                # Single value
                customization = slots['Customization']['value']['interpretedValue']
            elif isinstance(slots['Customization']['value'], list):
                # Multiple values
                customization = [item['interpretedValue'] for item in slots['Customization']['value']]
        
        print(f"Intent: {intent_name}, DishName: {dish_name}, Quantity: {quantity}, Customization: {customization}")
        
        # Store order in DynamoDB
        orders_table = dynamodb.Table(ORDERS_TABLE)
        order_id = f"ORD-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.datetime.now().isoformat()
        
        # Prepare order item
        order_item = {
            'OrderID': order_id,
            'Timestamp': timestamp,
            'DishName': dish_name,
            'Quantity': quantity,
            'Status': 'Pending'
        }
        
        # Add customization if present
        if customization:
            order_item['Customization'] = customization
        
        orders_table.put_item(Item=order_item)
        
        # Build notification message
        customization_text = ""
        if customization:
            if isinstance(customization, list):
                customization_text = f", 特殊要求: {', '.join(customization)}"
            else:
                customization_text = f", 特殊要求: {customization}"
        
        notification_message = f"菜品名称: {dish_name}, 数量: {quantity}{customization_text}, 状态: 待处理"
        
        # Send notification
        payload = {
            "default": "New order notification",
            "APNS_SANDBOX": json.dumps({
                "aps": {
                    "alert": {
                        "title": "New Order",
                        "body": notification_message
                    },
                    "sound": "default",
                    "badge": 1
                }
            })
        }
        
        sns_client.publish(
            TargetArn=endpoint_arn,
            MessageStructure='json',
            Message=json.dumps(payload)
        )
        
        # Build success response message
        success_message = f"Order for {quantity} {dish_name}"
        if customization:
            if isinstance(customization, list):
                success_message += f" with {', '.join(customization)}"
            else:
                success_message += f" with {customization}"
        success_message += " has been placed successfully."
        
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': intent_name,
                    'state': 'Fulfilled'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': success_message
                }
            ]
        }
    
    except KeyError as e:
        print(f"KeyError - Missing slot: {e}")
        print("Available slots:", list(slots.keys()) if 'slots' in locals() else "No slots found")
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'] if 'sessionState' in event else 'Unknown',
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': f"Missing required information: {str(e)}. Please try again."
                }
            ]
        }
    
    except Exception as e:
        print("Error:", e)
        return {
            'sessionState': {
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': event['sessionState']['intent']['name'] if 'sessionState' in event else 'Unknown',
                    'state': 'Failed'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': "An error occurred while placing your order. Please try again."
                }
            ]
        }