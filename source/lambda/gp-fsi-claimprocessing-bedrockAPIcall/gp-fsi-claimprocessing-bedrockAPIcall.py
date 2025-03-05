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
import datetime
import boto3
from random import random
import uuid
import botocore
import os

numb=round(random()*100000)

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


bedrock_agent_client = boto3.client('bedrock-agent-runtime')

#DDB_table_FM= os.environ["DDB_table_FM"]
DDB_table_FM= "GP-FSI-ClaimsProcessing-FM"
dynamodb = boto3.resource('dynamodb')

txt = "What is the Average Collision Repair cost"


def invokeFM(knowledgeBaseId,model_id,region_id,prompt):
    model_arn='arn:aws:bedrock:'+region_id+'::foundation-model/'+model_id
    response= bedrock_agent_client.retrieve_and_generate(
    input={'text': prompt},
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
    response_body=generated_text
    print(response_body)
    return response_body

def getFMModel(model_selected):
    table = dynamodb.Table(DDB_table_FM)
    response = table.get_item(
        Key={'Active': model_selected}
        )
    FMModeldata=response['Item']
    print(FMModeldata)
    knowledgeBaseId=FMModeldata['knowledgeBaseId']
    model_id=FMModeldata['model_id']
    region_id=FMModeldata['region_id']
    print(knowledgeBaseId, model_id, region_id)
    return knowledgeBaseId,model_id, region_id


def lambda_handler(event, context):
    print("starting")
    print(event)
    model_selected=event['model']
    print(model_selected) 
    prompt=event['query']
    print(prompt) 
    knowledgeBaseId,model_id, region_id=getFMModel(model_selected)
    response_body=invokeFM(knowledgeBaseId,model_id,region_id,prompt)
    print(response_body)

    return {
        'statusCode': 200,
        'data': {"body":response_body}
        }
