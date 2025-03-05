'''MIT No Attribution

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'''

import os
import boto3
import json
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Initialize environment variables
DDBtableCustomerInfo = os.environ["DDBtableCustomerInfo"]
OriginationIdentity = os.environ["SMS_Origination_number_ARN"]
User_Upload_URL = os.environ["CloudFront_URL"]+"/GP-FSI-Claims-Processing-Upload-Documents"

client = boto3.client('pinpoint-sms-voice-v2')

def customer_message(CustomerEndpoint, message):
    try:
        response = client.send_text_message(
            DestinationPhoneNumber=CustomerEndpoint,
            OriginationIdentity=OriginationIdentity,
            MessageBody=message,
            MessageType='TRANSACTIONAL'
        )
        print(f"SMS sent successfully: {response}")
        return response
    except ClientError as e:
        print(f"Error sending SMS: {e.response}")
        raise e

def dynamodb_getitem(Policy_VIN):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(DDBtableCustomerInfo)        
        response = table.get_item(
            Key={
                'Policy_VIN': Policy_VIN
            }
        )
        print(f"DynamoDB response: {response}")

        if 'Item' not in response:
            raise ValueError(f"No item found for Policy_VIN: {Policy_VIN}")

        item = response['Item']
        CustomerEndpoint = item['CustomerPhone']
        print(f"Customer endpoint: {CustomerEndpoint}")
        return CustomerEndpoint
    except ClientError as e:
        print(f"DynamoDB error: {e.response}")
        raise
    except KeyError as e:
        print(f"Missing required field in DynamoDB response: {str(e)}")
        raise

def parsing(SQSMessage):
    print(f"Parsing SQS message: {SQSMessage}")
    
    if "decision" in SQSMessage:
        print("Processing Case Status Notification")
        CaseNumber = SQSMessage.get('CaseNumber')  
        if not CaseNumber:
            raise ValueError("Missing CaseNumber in SQS message")
            
        decision = SQSMessage.get('decision')
        comments = SQSMessage.get('comments', 'No comments provided')
        message = f"Your claim {CaseNumber} is {decision}. Agent comment is {comments}"
        print(f"Generated message: {message}")
        return CaseNumber, message
    elif "OTP" in SQSMessage.get('Message', '').upper() or "CaseNumber" in SQSMessage:
        # Handle OTP message
        print("Processing OTP Notification")
        CaseNumber = SQSMessage.get('CaseNumber')
        message = SQSMessage.get('Message')
        if not CaseNumber or not message:
            raise ValueError("Missing required fields for OTP message")
        return CaseNumber, message
    else:
        raise ValueError("Unrecognized message format in SQS message")

def lambda_handler(event, context):
    try:
        print(f"Event: {event}")
        print(f"Context: {context}")
        message = ""
        CaseNumber = ""

        if "Records" in event:
            try:
                SQSMessage = json.loads(event['Records'][0]['body'])
                CaseNumber, message = parsing(SQSMessage)
                print(f"Parsed message: {message}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in SQS message: {str(e)}")
            except ValueError as e:
                raise ValueError(f"Error parsing SQS message: {str(e)}")
        else:
            # Handle Chatbot invocation
            print("Processing Claims Opening Notification")
            if 'Details' not in event or 'Parameters' not in event['Details'] or 'Lexdata' not in event['Details']['Parameters']:
                raise ValueError("Invalid event structure for Chatbot invocation")
                
            CaseNumber = event['Details']['Parameters']['Lexdata']
            message = f"Claims processing: Upload supporting documents to {User_Upload_URL}, use Claims number {CaseNumber} to validate"
            print(f"Generated Chatbot message: {message}")

        if not CaseNumber:
            raise ValueError("CaseNumber is missing or invalid")

        Policy_VIN = CaseNumber.split("-")[0]
        print(f"Policy_VIN: {Policy_VIN}")
        
        CustomerEndpoint = dynamodb_getitem(Policy_VIN)
        print(f"Using OriginationIdentity: {OriginationIdentity}")
        print("Invoking message sending")
        
        response = customer_message(CustomerEndpoint, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'Success',
                'messageId': response.get('MessageId', ''),
                'caseNumber': CaseNumber,
                'message': message
            })
        }

    except Exception as e:
        error_message = str(e)
        print(f"Error in lambda_handler: {error_message}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message,
                'errorType': type(e).__name__,
                'event': event
            })
        }
