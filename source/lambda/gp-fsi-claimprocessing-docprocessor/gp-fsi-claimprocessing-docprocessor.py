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

import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
import base64
import io
from datetime import datetime
from botocore.exceptions import ClientError
import random
import time

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')
bedrock_agent_client = boto3.client('bedrock-agent-runtime')

DDB_table_NewClaim = os.environ["DDB_table_NewClaim"]
DDB_table_FM= os.environ["DDB_table_FM"]
DDB_table_VehiclePricing= os.environ["DDB_table_VehiclePricing"]


def exponential_backoff_retry(max_retries=5, initial_delay=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for retry in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ThrottlingException':
                        if retry == max_retries - 1:
                            raise
                        # Add jitter to prevent synchronized retries
                        sleep_time = delay + random.uniform(0, 1)
                        time.sleep(sleep_time)
                        delay *= 10  # Exponential backoff
                    else:
                        raise
        return wrapper
    return decorator

def llm_updateitem(CaseNumber,response_body):
    table = dynamodb.Table(DDB_table_NewClaim)
    response = table.update_item(
        Key={
            'CaseNumber': CaseNumber
        },
        UpdateExpression="set GenAI_Summary=:m ,case_status=:c",
        ExpressionAttributeValues={
            ':m': response_body,
            ':c': "Review",
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

@exponential_backoff_retry()
def invokeFM(knowledgeBaseId,model_id,region_id,vehicledata,Combined_vehicle_image_analysis_output,Summary_prompt):
    model_arn='arn:aws:bedrock:'+region_id+'::foundation-model/'+model_id
    vehicledata=str(vehicledata)
    if knowledgeBaseId:
        #print(knowledgeBaseId)
        #print(model_id)
        #print(region_id)
        #print(vehicledata)
        #print(Combined_vehicle_image_analysis_output)
        #print(Summary_prompt)
        response= bedrock_agent_client.retrieve_and_generate(
        input={'text': "Combined_vehicle_image_analysis_output is "+str(Combined_vehicle_image_analysis_output)+Summary_prompt},
        retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                'knowledgeBaseId': knowledgeBaseId,
                'modelArn': model_arn
        }
        }
        )
        print(response)
        metadata_response=response['ResponseMetadata']
        generated_text = response['output']['text']
        response_body=generated_text.replace("$","$")
        print(response_body)
        return response_body
    else:
        print("knowledgeBaseId is empty. Cannot generate final summarization. Update the knowledge base id to be used in the Metadata table named GP-FSI-ClaimsProcessing-FM ")
        exit()

@exponential_backoff_retry()
def combine_image_analysis(CaseNumber,Image_Combine_prompt,model_id):
    table = dynamodb.Table(DDB_table_NewClaim)
    response = table.get_item(
                Key={'CaseNumber': CaseNumber}
            )
    #print(response)
    VehiclceAnalysis=response['Item']['VehiclceAnalysis']
    print(VehiclceAnalysis)
    # Image_Combine_prompt_input="These are the vehicle image results "+str(VehiclceAnalysis)+". "+Image_Combine_prompt
    # prompt = {
    #     "anthropic_version": "bedrock-2023-05-31",
    #     "max_tokens": 1000,
    #     "temperature": 0.5,
    #     "messages": [
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "text",
    #                     "text": Image_Combine_prompt_input
    #                 }
    #             ]
    #         }
    #     ]
    # }
    # json_prompt = json.dumps(prompt)
    # response = bedrock_client.invoke_model(body=json_prompt, modelId=model_id,
    #                                 accept="application/json", contentType="application/json")
    # response_body = json.loads(response.get('body').read())
    Image_Combine_prompt_input = "These are the vehicle image results "+str(VehiclceAnalysis)+". "+Image_Combine_prompt
    print(Image_Combine_prompt_input)
    request = {
        'modelId': model_id,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'text': Image_Combine_prompt_input
                    }
                ]
            }
        ]
    }

    response = bedrock_client.converse(**request)
    Combined_vehicle_image_analysis_output = response['output']['message']['content'][0]['text']


    #Combined_vehicle_image_analysis_output = response_body.replace("$","\\$")
    # returning the final string to the end user
    print(Combined_vehicle_image_analysis_output) 
    response = table.update_item(
    Key={
            'CaseNumber': CaseNumber
        },
        UpdateExpression="set Combined_vehicle_image_analysis_output=:m",
        ExpressionAttributeValues={
            ':m': Combined_vehicle_image_analysis_output,
        },
        ReturnValues="UPDATED_NEW"
    )
    return Combined_vehicle_image_analysis_output



def license_analysis(CaseNumber,bucket,key,CustomerName):
    table = dynamodb.Table(DDB_table_NewClaim)
    
    client = boto3.client('textract')
    response = client.analyze_id(
    DocumentPages=[
        {
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        ]
    )

    IdentityDocumentFields=response[ 'IdentityDocuments'][0]['IdentityDocumentFields']
    #print(IdentityDocumentFields)
    FIRST_NAME=""
    LAST_NAME=""
    for fields in IdentityDocumentFields:
        #print(fields)
        if "FIRST_NAME"==fields['Type']['Text']:
            FIRST_NAME=fields['ValueDetection']['Text']

        if "LAST_NAME"==fields['Type']['Text']:
            LAST_NAME=fields['ValueDetection']['Text']
        if "EXPIRATION_DATE"==fields['Type']['Text']:
            EXPIRATION_DATE=fields['ValueDetection']['Text']
    License_vaidate=""    
    if CustomerName.lower()==(FIRST_NAME+" "+LAST_NAME).lower():
        License_vaidate=FIRST_NAME+" "+LAST_NAME + "- first Name and Last Name matching with the License uploaded"
    elif CustomerName.lower()==(LAST_NAME+" "+FIRST_NAME).lower():
        License_vaidate=LAST_NAME+" "+FIRST_NAME + "- first Name and Last Name matching with the License uploaded"
    else:
        License_vaidate=FIRST_NAME+" "+LAST_NAME + "- First Name and Last Name not matching with the License uploaded"
    #print(datetime.now().strftime('%m/%d/%Y'))
    if datetime.strptime(EXPIRATION_DATE,'%m/%d/%Y').date().strftime('%m/%d/%Y') <datetime.now().strftime('%m/%d/%Y'):
        License_vaidate="Valid License - expiration date "+EXPIRATION_DATE+";"+License_vaidate
    else:
        License_vaidate="Expired License - expiration date "+EXPIRATION_DATE+";"+License_vaidate
    
    print(License_vaidate)
    response = table.update_item(
    Key={
            'CaseNumber': CaseNumber
        },
        UpdateExpression="set License_vaidate=:m, case_status=:c",
        ExpressionAttributeValues={
            ':m': License_vaidate,
            ':c': "License Uploaded, waiting for Vehicle Images",
        },
        ReturnValues="UPDATED_NEW"
    )
    return License_vaidate


def image_analysis_updateitem(CaseNumber,s3_object,image_analysis_output,FileNameWE):
    table = dynamodb.Table(DDB_table_NewClaim)

    image=s3_object.split("/")[-1].split(".")[0].replace("-","")
    print(image)
    response = table.update_item(
                Key={
                    "CaseNumber": CaseNumber
                },
                UpdateExpression="set VehiclceAnalysis."+image+" = :Analysis1",
                    ExpressionAttributeValues={
                    ':Analysis1': {s3_object:image_analysis_output}
                    },
                ReturnValues="UPDATED_NEW"
    )

    return response

@exponential_backoff_retry()
def image_analysis(file_type,image_base64,model_id,Image_prompt,vehicledata):
    Image_prompt="Vehicle parts data is "+str(vehicledata)+"."+Image_prompt
    image_bytes = base64.b64decode(image_base64)
    # prompt = {
    #     "anthropic_version": "bedrock-2023-05-31",
    #     "max_tokens": 1000,
    #     "temperature": 0.5,
    #     "system": Image_prompt,
    #     "messages": [
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "image",
    #                     "source": {
    #                         "type": "base64",
    #                         "media_type": file_type,
    #                         "data": image_base64
    #                     }
    #                 },
    #                 {
    #                     "type": "text",
    #                     "text": Image_prompt
    #                 }
    #             ]
    #         }
    #     ]
    # }
    # json_prompt = json.dumps(prompt)
    # response = bedrock_client.invoke_model(body=json_prompt, modelId=model_id,
    #                                 accept="application/json", contentType="application/json")
    # # getting the response from Claude3 and parsing it to return to the end user
    # response_body = json.loads(response.get('body').read())
    # # the final string returned to the end user
    # image_analysis_output = response_body['content'][0]['text'].replace("$","\\$")
    # # returning the final string to the end user
    # #print(image_llm_output) 

    # Construct the request using Converse API structure
    print(model_id)
    request = {
        'modelId': model_id,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'image': {
                            'format': file_type.split('/')[-1],  # Extract format from media_type
                            'source': {
                                'bytes': image_bytes
                            }
                        }
                    },
                    {
                        'text': Image_prompt
                    }
                ]
            }
        ]
    }

    # Make the API call using converse instead of invoke_model
    response = bedrock_client.converse(**request)
    print(response)
    # Parse JSON
    #data = json.loads(response)
    # Extract text field
    image_analysis_output = response['output']['message']['content'][0]['text']
    print(image_analysis_output)
    return image_analysis_output


def image_base64_encoder(bucket,key,FileExtension):

    response = s3.get_object(Bucket=bucket, Key=""+key+"")
    print(response)
    file_content = response['Body'].read()
    file_type='image/'+FileExtension
    # Convert the file content to base64
    image_base64 = base64.b64encode(file_content).decode('utf-8')
    #print(image_base64)
    return file_type,image_base64

def getFMModel():
    table = dynamodb.Table(DDB_table_FM)
    response = table.get_item(
        Key={'Active': 'Y'}
        )
    FMModeldata=response['Item']
    print(FMModeldata)
    knowledgeBaseId=FMModeldata['knowledgeBaseId']
    model_id=FMModeldata['model_id']
    region_id=FMModeldata['region_id']
    Image_prompt=FMModeldata['Image_prompt']
    Image_Combine_prompt=FMModeldata['Image_Combine_prompt']
    Summary_prompt=FMModeldata['Summary_prompt']
    
    print(knowledgeBaseId, model_id, region_id,Image_prompt)
    return Image_prompt,knowledgeBaseId,model_id, region_id,Image_Combine_prompt,Summary_prompt


def getpartsdata(CarMake_Model):
    table = dynamodb.Table(DDB_table_VehiclePricing)
    response = table.get_item(
        Key={'CarMake_Model': CarMake_Model
            }
        )
    vehicledata=response['Item']
    print(vehicledata)
    return vehicledata

def getclaimdata(CaseNumber):
    table = dynamodb.Table(DDB_table_NewClaim)
    response = table.get_item(
                Key={'CaseNumber': CaseNumber}
            )
    print(response)
    CarMake_Model=response['Item']['CarMake_Model']
    CustomerName=response['Item']['CustomerName']
    return CarMake_Model,CustomerName

def lambda_handler(event, context):

    bucket=event['Records'][0]['s3']['bucket']['name']
    key=event['Records'][0]['s3']['object']['key']
    s3_object="s3://"+bucket+"/"+key
    CaseNumber=key.split("/")[1]
    FileName=key.split("/")[2]
    FileNameWE=key.split("/")[2].split(".")[0]
    FileExtension=key.split("/")[2].split(".")[1]
    print(s3_object,bucket,CaseNumber,FileName,FileExtension)
    CarMake_Model,CustomerName=getclaimdata(CaseNumber)
    print(CarMake_Model,CustomerName)
    vehicledata=getpartsdata(CarMake_Model)
    print(vehicledata)
    Image_prompt, knowledgeBaseId, model_id, region_id,Image_Combine_prompt,Summary_prompt=getFMModel()
    print(Image_prompt, knowledgeBaseId, model_id, region_id,Image_Combine_prompt)
    file_type,image_base64=image_base64_encoder(bucket,key,FileExtension)
    print(file_type,image_base64)

    if "license" in FileName:
        print("License file")
        license_analysis(CaseNumber,bucket,key,CustomerName)
    elif "vehicle" in FileName:
        image_analysis_output=image_analysis(file_type,image_base64,model_id,Image_prompt,vehicledata)
        print(image_analysis_output)
        image_analysis_updateitem(CaseNumber,s3_object,image_analysis_output,FileNameWE)
        if "vehicle1" in FileName:
            Combined_vehicle_image_analysis_output=combine_image_analysis(CaseNumber,Image_Combine_prompt,model_id)
            print(Combined_vehicle_image_analysis_output)
            response_body=invokeFM(knowledgeBaseId,model_id,region_id,vehicledata,Combined_vehicle_image_analysis_output,Summary_prompt)
            print(response_body)
            response_body=llm_updateitem(CaseNumber,response_body)
            print(response_body)
        else:
            print("More files to process")
    elif "incidentreport" in FileName:
        print("Incident file, build your file processing logic") 
    elif "medical-report" in FileName:    
        print("medical-report build your file processing logic")