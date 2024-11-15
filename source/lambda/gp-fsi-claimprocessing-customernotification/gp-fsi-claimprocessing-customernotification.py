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
#use this if you are using pinpoint from the same account
pinpoint_client=boto3.client('pinpoint')
#use this if you are using pinpoint from a different account
#pinpoint_client = boto3.client('pinpoint',aws_access_key_id="<replace this>",aws_secret_access_key="<replace this>",region_name="us-east-1")

DDB_table_NewClaim = os.environ["DDB_table_NewClaim"]
Pinpoint_app_id= os.environ["Pinpoint_app_id"]
Pinpoint_origination_number= os.environ["Pinpoint_origination_number"]
User_Upload_URL = os.environ["CloudFront_URL"]+"/GP-FSI-Claims-Processing-Upload-Documents"

#https://d2a04v3dgsrdy.cloudfront.net/GP-FSI-Claims-Processing-Upload-Documents

def dynamodb_getitem(CaseNumber):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DDB_table_NewClaim)        
    response = table.get_item(
        Key={
                'CaseNumber': CaseNumber
            }
        )
    print(response)

    item=response['Item']
    CustomerEndpoint = item['CustomerPhone']
    print(CustomerEndpoint)
    return CustomerEndpoint

def lambda_handler(event, context):
    # Extract contact data from the event
    print(event,context)
    if "Records" in event:
        SQSMessage=event['Records'][0]['body']
        CaseNumber=SQSMessage.split("-Decsion")[0]
        print(CaseNumber)
        message="Decsion "+SQSMessage.split("-Decsion")[1]
    else:
        CaseNumber = event['Details']['Parameters']['Lexdata']
        message = ("Claims processing: Upload  supporting documents to "+User_Upload_URL+", use Claims number "+CaseNumber+" to validate")

    CustomerEndpoint=dynamodb_getitem(CaseNumber)
    

    app_id = Pinpoint_app_id
    origination_number = Pinpoint_origination_number
    message = message
    message_type = "TRANSACTIONAL"
    try:
        response = pinpoint_client.send_messages(
            ApplicationId=app_id,
            MessageRequest={
                'Addresses': {CustomerEndpoint: {'ChannelType': 'SMS'}},
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'MessageType': message_type,
                        'OriginationNumber': origination_number}}})
        print(response)
    except :
        print("Not able to send the message")

    
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }



    

