import json
import os
import boto3
from botocore.exceptions import ClientError
import pprint
import random
from retrying import retry
import requests
import time
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, RequestError
#from utility import create_bedrock_execution_role, create_oss_policy_attach_bedrock_execution_role, create_policies_in_oss, interactive_sleep
suffix = random.randrange(200, 900)
boto3_session = boto3.session.Session()
#region_name = boto3_session.region_name

suffix = random.randrange(200, 900)
boto3_session = boto3.session.Session()

iam_client = boto3_session.client('iam')
account_id = boto3.client('sts').get_caller_identity().get('Account')
identity = boto3.client('sts').get_caller_identity()['Arn']
s3_client = boto3.client('s3')
bucket_name = f'gp-fsi-claims-processing{account_id}' # replace it with your bucket name.
local_directory = "Knowledgebase/"
s3_prefix = "Knowledgebase/"

region_name = "us-east-1"  # default region

def  update_kb_FM(knowledgeBaseId): 
    dynamodb = boto3.resource('dynamodb')
    DDBtableFM=os.environ['DDBtableFM']
    table = dynamodb.Table(DDBtableFM)
    response = table.update_item(
        Key={
            'Active': "Y"
        },
        UpdateExpression="set knowledgeBaseId=:m",
        ExpressionAttributeValues={
            ':m': knowledgeBaseId
        },
        ReturnValues="UPDATED_NEW"
        )

try:
    s3_client.head_bucket(Bucket=bucket_name)
    print(f'Bucket {bucket_name} Exists')
    response = s3_client.get_bucket_location(Bucket=bucket_name)
    print(response)
    
    # Handle the special case for us-east-1
    location_constraint = response['LocationConstraint']
    if location_constraint is None:
        region_name = "us-east-1"
    else:
        region_name = location_constraint
        
    print(f"Region name: {region_name}")
    os.environ['AWS_DEFAULT_REGION'] = region_name
    
except Exception as e:
    print(f"Error: {str(e)}")

print(f"Identity: {identity}")
print(f"Account ID: {account_id}")
print(f"Region: {region_name}")

encryption_policy_name = f"gp-fsi-claims-processing-sp-{suffix}"
network_policy_name = f"gp-fsi-claims-processing-np-{suffix}"
access_policy_name = f'gp-fsi-claims-processing-ap-{suffix}'
bedrock_execution_role_name = f'AmazonBedrockExeRoleforKB_gp_fsi_claimsprocessing_{suffix}'
fm_policy_name = f'AmazonBedrockFoundationModelPolicyForKB_gp_fsi_claimsprocessing_{suffix}'
s3_policy_name = f'AmazonBedrockS3PolicyForKB_gp_fsi_claimsprocessing_{suffix}'
oss_policy_name = f'AmazonBedrockOSSPolicyForKB_gp_fsi_claimsprocessing_{suffix}'



service = 'aoss'
aoss_client=boto3.client('opensearchserverless')
iam_client = boto3.client('iam')
bedrock_agent_client = boto3.client('bedrock-agent')
suffix = random.randrange(200, 900)

pp = pprint.PrettyPrinter(indent=2)
vector_store_name = f'gp-fsi-claims-processing'
index_name = f"gp-fsi-claims-processing-index"


def upload_directory_to_s3(local_directory, bucket_name, s3_prefix):

    
    # Specify the local directory containing the Knowledge base files
    local_asset_dir = os.path.join(os.getcwd(), local_directory)
    print(f"Local directory: {local_asset_dir}")

    # Walk through the local directory
    for root, dirs, files in os.walk(local_asset_dir):
        for file in files:
            local_path = os.path.join(root, file)
            
            # Calculate relative path
            relative_path = os.path.relpath(local_path, local_asset_dir)
            s3_path = os.path.join(s3_prefix, relative_path).replace("\\", "/")

            # Upload the file
            try:
                print(f"Uploading {local_path} to s3://{bucket_name}/{s3_path}")
                s3_client.upload_file(local_path, bucket_name, s3_path)
            except ClientError as e:
                print(f"Error uploading {local_path}: {str(e)}")


def check_knowledge_base_exists(bedrock_client, kb_name):
    try:
        response = bedrock_client.list_knowledge_bases()
        for kb in response['knowledgeBaseSummaries']:
            if kb['name'] == kb_name:
                update_kb_FM(kb['knowledgeBaseId'])
                return True, kb['knowledgeBaseId']
    except Exception as e:
        print(f"Error checking for existing knowledge base: {str(e)}")
    return False, None

def create_bedrock_execution_role(bucket_name):
    foundation_model_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                ],
                "Resource": [
                    f"arn:aws:bedrock:{region_name}::foundation-model/amazon.titan-embed-text-v2:0"
                ]
            }
        ]
    }

    s3_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "StringEquals": {
                        "aws:ResourceAccount": f"{account_id}"
                    }
                }
            }
        ]
    }

    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    # create policies based on the policy documents
    fm_policy = iam_client.create_policy(
        PolicyName=fm_policy_name,
        PolicyDocument=json.dumps(foundation_model_policy_document),
        Description='Policy for accessing foundation model',
    )

    s3_policy = iam_client.create_policy(
        PolicyName=s3_policy_name,
        PolicyDocument=json.dumps(s3_policy_document),
        Description='Policy for reading documents from s3')

    # create bedrock execution role
    bedrock_kb_execution_role = iam_client.create_role(
        RoleName=bedrock_execution_role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
        Description='Amazon Bedrock Knowledge Base Execution Role for accessing OSS and S3',
        MaxSessionDuration=3600
    )

    # fetch arn of the policies and role created above
    bedrock_kb_execution_role_arn = bedrock_kb_execution_role['Role']['Arn']
    s3_policy_arn = s3_policy["Policy"]["Arn"]
    fm_policy_arn = fm_policy["Policy"]["Arn"]

    # attach policies to Amazon Bedrock execution role
    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"],
        PolicyArn=fm_policy_arn
    )
    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"],
        PolicyArn=s3_policy_arn
    )
    return bedrock_kb_execution_role


def create_oss_policy_attach_bedrock_execution_role(collection_id, bedrock_kb_execution_role):
    # define oss policy document
    oss_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll"
                ],
                "Resource": [
                    f"arn:aws:aoss:{region_name}:{account_id}:collection/{collection_id}"
                ]
            }
        ]
    }
    oss_policy = iam_client.create_policy(
        PolicyName=oss_policy_name,
        PolicyDocument=json.dumps(oss_policy_document),
        Description='Policy for accessing opensearch serverless',
    )
    oss_policy_arn = oss_policy["Policy"]["Arn"]
    print("Opensearch serverless arn: ", oss_policy_arn)

    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"],
        PolicyArn=oss_policy_arn
    )
    return None


def create_policies_in_oss(vector_store_name, aoss_client, bedrock_kb_execution_role_arn):
    encryption_policy = aoss_client.create_security_policy(
        name=encryption_policy_name,
        policy=json.dumps(
            {
                'Rules': [{'Resource': ['collection/' + vector_store_name],
                           'ResourceType': 'collection'}],
                'AWSOwnedKey': True
            }),
        type='encryption'
    )

    network_policy = aoss_client.create_security_policy(
        name=network_policy_name,
        policy=json.dumps(
            [
                {'Rules': [{'Resource': ['collection/' + vector_store_name],
                            'ResourceType': 'collection'}],
                 'AllowFromPublic': True}
            ]),
        type='network'
    )
    access_policy = aoss_client.create_access_policy(
        name=access_policy_name,
        policy=json.dumps(
            [
                {
                    'Rules': [
                        {
                            'Resource': ['collection/' + vector_store_name],
                            'Permission': [
                                'aoss:CreateCollectionItems',
                                'aoss:DeleteCollectionItems',
                                'aoss:UpdateCollectionItems',
                                'aoss:DescribeCollectionItems'],
                            'ResourceType': 'collection'
                        },
                        {
                            'Resource': ['index/' + vector_store_name + '/*'],
                            'Permission': [
                                'aoss:CreateIndex',
                                'aoss:DeleteIndex',
                                'aoss:UpdateIndex',
                                'aoss:DescribeIndex',
                                'aoss:ReadDocument',
                                'aoss:WriteDocument'],
                            'ResourceType': 'index'
                        }],
                    'Principal': [ identity, bedrock_kb_execution_role_arn],
                    'Description': 'Easy data policy'}
            ]),
        type='data'
    )
    return encryption_policy, network_policy, access_policy


def delete_iam_role_and_policies():
    fm_policy_arn = f"arn:aws:iam::{account_id}:policy/{fm_policy_name}"
    s3_policy_arn = f"arn:aws:iam::{account_id}:policy/{s3_policy_name}"
    oss_policy_arn = f"arn:aws:iam::{account_id}:policy/{oss_policy_name}"
    iam_client.detach_role_policy(
        RoleName=bedrock_execution_role_name,
        PolicyArn=s3_policy_arn
    )
    iam_client.detach_role_policy(
        RoleName=bedrock_execution_role_name,
        PolicyArn=fm_policy_arn
    )
    iam_client.detach_role_policy(
        RoleName=bedrock_execution_role_name,
        PolicyArn=oss_policy_arn
    )
    iam_client.delete_role(RoleName=bedrock_execution_role_name)
    iam_client.delete_policy(PolicyArn=s3_policy_arn)
    iam_client.delete_policy(PolicyArn=fm_policy_arn)
    iam_client.delete_policy(PolicyArn=oss_policy_arn)
    return 0


def interactive_sleep(seconds: int):
    dots = ''
    for i in range(seconds):
        dots += '.'
        print(dots, end='\r')
        time.sleep(1)
    # print('Done!')

'''    
def create_bukcet (bucket_name,region_name):

    # Check if bucket exists, and if not create S3 bucket for knowledge base data source
    try:
        s3_client = boto3.client('s3')
        s3_client.head_bucket(Bucket=bucket_name)
        print(f'Bucket {bucket_name} Exists')
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        region_name=response['LocationConstraint']
        if location_constraint is None:
            region_name = "us-east-1"
        else:
            region_name = location_constraint
        print(response['LocationConstraint'])
        os.environ['AWS_DEFAULT_REGION'] = region_name
    except ClientError as e:
        print(f'Creating bucket {bucket_name}')
        if region_name == "us-east-1":
            s3bucket = s3_client.create_bucket(Bucket=bucket_name)
            response = s3_client.get_bucket_location(Bucket=bucket_name)
            region_name=response['LocationConstraint']
            print(response['LocationConstraint'])
            os.environ['AWS_DEFAULT_REGION'] = region_name
        else:
            s3bucket = s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={ 'LocationConstraint': region_name }
        )
    # The data source to ingest documents from, into the OpenSearch serverless knowledge base index
    s3Configuration = {
        "bucketArn": f"arn:aws:s3:::{bucket_name}",
        "inclusionPrefixes":["Knowledgebase/"] # you can use this if you want to create a KB using data within s3 prefixes.
    }   
    
    return s3Configuration
'''    
def setup_aos(bedrock_kb_execution_role,bedrock_kb_execution_role_arn):

    credentials = boto3.Session().get_credentials()
    awsauth = auth = AWSV4SignerAuth(credentials, region_name, service)
    # create security, network and data access policies within OSS
    encryption_policy, network_policy, access_policy = create_policies_in_oss(vector_store_name=vector_store_name,
                           aoss_client=aoss_client,
                           bedrock_kb_execution_role_arn=bedrock_kb_execution_role_arn)
    collection = aoss_client.create_collection(name=vector_store_name,type='VECTORSEARCH',tags=[
        {
            'key': 'createdby',
            'value': 'Claims-processing-guidance-package-deployment'
        },
    
    ])
    
    pp.pprint(collection)
    
    # Get the OpenSearch serverless collection URL
    collection_id = collection['createCollectionDetail']['id']
    host = collection_id + '.' + region_name + '.aoss.amazonaws.com'
    print(host)

    # wait for collection creation
    # This can take couple of minutes to finish
    response = aoss_client.batch_get_collection(names=[vector_store_name])
    # Periodically check collection status
    while (response['collectionDetails'][0]['status']) == 'CREATING':
        print('Creating collection...')
        interactive_sleep(30)
        response = aoss_client.batch_get_collection(names=[vector_store_name])
    print('\nCollection successfully created:')
    pp.pprint(response["collectionDetails"])
    
    # create opensearch serverless access policy and attach it to Bedrock execution role
    try:
        create_oss_policy_attach_bedrock_execution_role(collection_id=collection_id,
                                                        bedrock_kb_execution_role=bedrock_kb_execution_role)
        # It can take up to a minute for data access rules to be enforced
        interactive_sleep(60)
    except Exception as e:
        print("Policy already exists")
        pp.pprint(e)


    index_name = f"gp-fsi-claims-processing-index"
    body_json = {
       "settings": {
          "index.knn": "true",
           "number_of_shards": 1,
           "knn.algo_param.ef_search": 512,
           "number_of_replicas": 0,
       },
       "mappings": {
          "properties": {
             "vector": {
                "type": "knn_vector",
                "dimension": 1024 ,
                 "method": {
                     "name": "hnsw",
                     "engine": "faiss",
                     "space_type": "l2"
                 },
             },
             "text": {
                "type": "text"
             },
             "text-metadata": {
                "type": "text"         }
          }
       }
    }

    # Build the OpenSearch client
    oss_client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300
    )

    # Create index
    try:
        response = oss_client.indices.create(index=index_name, body=json.dumps(body_json))
        print('\nCreating index:')
        pp.pprint(response)
    
        # index creation can take up to a minute
        interactive_sleep(60)
    except RequestError as e:
        # you can delete the index if its already exists
        # oss_client.indices.delete(index=index_name)
        print(f'Error while trying to create the index, with error {e.error}\nyou may unmark the delete above to delete, and recreate the index')
    
    opensearchServerlessConfiguration = {
                "collectionArn": collection["createCollectionDetail"]['arn'],
                "vectorIndexName": index_name,
                "fieldMapping": {
                    "vectorField": "vector",
                    "textField": "text",
                    "metadataField": "text-metadata"
                }
            }
    #print(opensearchServerlessConfiguration)
    # Ingest strategy - How to ingest data from the data source
    chunkingStrategyConfiguration = {
        "chunkingStrategy": "FIXED_SIZE",
        "fixedSizeChunkingConfiguration": {
            "maxTokens": 512,
            "overlapPercentage": 20
        }
    }
    #print(chunkingStrategyConfiguration)
    return opensearchServerlessConfiguration,chunkingStrategyConfiguration


def create_kbse(kb_name,opensearchServerlessConfiguration,chunkingStrategyConfiguration,s3Configuration,bedrock_kb_execution_role_arn):
        
    # The embedding model used by Bedrock to embed ingested documents, and realtime prompts
    embeddingModelArn = f"arn:aws:bedrock:{region_name}::foundation-model/amazon.titan-embed-text-v2:0"
    
    name = kb_name
    description = "Amazon shareholder letter knowledge base."
    roleArn = bedrock_kb_execution_role_arn
    

    create_kb_response = bedrock_agent_client.create_knowledge_base(
            name = name,
            description = description,
            roleArn = roleArn,
            knowledgeBaseConfiguration = {
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": embeddingModelArn
                }
            },
            storageConfiguration = {
                "type": "OPENSEARCH_SERVERLESS",
                "opensearchServerlessConfiguration":opensearchServerlessConfiguration
            },
            tags={
            'createdby': 'Claims-processing-guidance-package-deployment'},
            )
    knowledgeBaseArn=create_kb_response["knowledgeBase"]['knowledgeBaseArn']
    knowledgeBaseId=create_kb_response["knowledgeBase"]['knowledgeBaseId']
    print(knowledgeBaseId,knowledgeBaseArn)


    # Create a DataSource in KnowledgeBase 
    create_ds_response = bedrock_agent_client.create_data_source(
        name = name,
        dataDeletionPolicy='RETAIN',
        description = description,
        knowledgeBaseId = knowledgeBaseId,
        dataSourceConfiguration = {
            "type": "S3",
            "s3Configuration":s3Configuration
        },
        vectorIngestionConfiguration = {
            "chunkingConfiguration": chunkingStrategyConfiguration
        }
    )
    dataSourceId=create_ds_response["dataSource"]['dataSourceId']
    print(dataSourceId)
    
    
    return knowledgeBaseId,dataSourceId
  
def ingestion (knowledgeBaseId,dataSourceId):
    # Start an ingestion job
    interactive_sleep(30)
    start_job_response = bedrock_agent_client.start_ingestion_job(knowledgeBaseId = knowledgeBaseId, dataSourceId = dataSourceId)
    job = start_job_response["ingestionJob"]
    pp.pprint(job)
    # Get job 
    while(job['status']!='COMPLETE' ):
        get_job_response = bedrock_agent_client.get_ingestion_job(
        knowledgeBaseId = knowledgeBaseId,
        dataSourceId = dataSourceId,
        ingestionJobId = job["ingestionJobId"]
        )
        job = get_job_response["ingestionJob"]
        
        interactive_sleep(30)
        pp.pprint(job)
        return knowledgeBaseId

def main():
    
    #s3Configuration=create_bukcet (bucket_name,region_name)
    s3Configuration = {
        "bucketArn": f"arn:aws:s3:::{bucket_name}",
        "inclusionPrefixes":["Knowledgebase/"] # you can use this if you want to create a KB using data within s3 prefixes.
    }  

    print(s3Configuration)
    upload_directory_to_s3(local_directory, bucket_name, s3_prefix)

    bedrock_client = boto3.client('bedrock-agent')
    kb_name = "gp-fsi-claims-processing-knowledge-base"

    # Check if the knowledge base already exists
    exists, existing_kb_id = check_knowledge_base_exists(bedrock_client, kb_name)
    if exists:
        print(f"Knowledge base '{kb_name}' already exists with ID: {existing_kb_id}")
        return existing_kb_id



    bedrock_kb_execution_role = create_bedrock_execution_role(bucket_name=bucket_name)
    bedrock_kb_execution_role_arn = bedrock_kb_execution_role['Role']['Arn']

    opensearchServerlessConfiguration,chunkingStrategyConfiguration=setup_aos(bedrock_kb_execution_role,bedrock_kb_execution_role_arn)
    print(opensearchServerlessConfiguration)
    print(chunkingStrategyConfiguration)
    knowledgeBaseId,dataSourceId=create_kbse(kb_name,opensearchServerlessConfiguration,chunkingStrategyConfiguration,s3Configuration,bedrock_kb_execution_role_arn)
    print(knowledgeBaseId,dataSourceId)
    knowledgeBaseId=ingestion (knowledgeBaseId,dataSourceId)
    print("Creating Knowledge base completed, note down the knowldge base id")
    print(knowledgeBaseId)
    update_kb_FM(knowledgeBaseId)
    print("Updated Claims processing FM tables with knowldge base id")
main()
