import os
import boto3
import time
import pprint
from botocore.exceptions import ClientError
import requests

'''Load sample data to DynamoDB tables'''
pp = pprint.PrettyPrinter(indent=2)

account_id = boto3.client('sts').get_caller_identity().get('Account')
identity = boto3.client('sts').get_caller_identity()['Arn']
s3_client = boto3.client('s3')
bucket_name = f'gp-fsi-claims-processing-{account_id}' # replace it with your bucket name.
local_directory = "Knowledgebase/"
s3_prefix = "Knowledgebase/"
region_name = "us-east-1"  # default region
region_name=os.environ['AWS_REGION']


print(f"Identity: {identity}")
print(f"Account ID: {account_id}")
print(f"Region: {region_name}")

DDBtableFM=os.environ['DDBtableFM']
DDBtableVehiclePricing=os.environ['DDBtableVehiclePricing']
DDBtableCustomerInfo=os.environ['DDBtableCustomerInfo']
BedrockKBID=os.environ['BedrockKBID']
CustomerPhone=os.environ['CustomerPhone']
SOCOTRA_External_PolicyHolderId1=os.environ['SOCOTRA_External_PolicyHolderId1']
SOCOTRA_External_PolicyHolderId2=os.environ['SOCOTRA_External_PolicyHolderId2']
SOCOTRA_External_PolicyHolderId3=os.environ['SOCOTRA_External_PolicyHolderId3']
SOCOTRA_External_PolicyHolderId4=os.environ['SOCOTRA_External_PolicyHolderId4']
DDBtableNewClaim=os.environ['DDBtableNewClaim']

bedrock_agent_client = boto3.client('bedrock-agent')

lex_client = boto3.client('lexv2-models')
client = boto3.client('lex-models')
# Create a pre-signed S3 URL to upload the bot archive
tagclient = boto3.client('resourcegroupstaggingapi')


def create_cognito_user(user_pool_id, username, email, temporary_password):
    client = boto3.client('cognito-idp')
    
    try:
        response = client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                }
            ],
            TemporaryPassword=temporary_password,
            MessageAction='SUPPRESS'  # Prevents sending welcome email
        )
        print(f"User {email} created successfully with the temporory password {temporary_password} ")
    except:
        print(f"Failed to create user {username}. If you are running it for the second time the user {username}/{email} may already exists. Use the temporory password {temporary_password} ")

def getAPIInfo():
    client = boto3.client('cloudformation')

    response = client.list_stack_resources(
    StackName='ClaimsProcessingStack1'
    )

    #print(response)
    stackinfo=response['StackResourceSummaries']
    for values in stackinfo:
        #print(values['ResourceType'],"-",values['LogicalResourceId'],"-",values['PhysicalResourceId'])
        if "AWS::ApiGateway::RestApi"==values['ResourceType']:
            api_url=f"https://{values['PhysicalResourceId']}.execute-api.{region_name}.amazonaws.com/dev/lambda" 
            print(api_url)
        if "AWS::Bedrock::KnowledgeBase"==values['ResourceType']:
            BedrockKBID=f"{values['PhysicalResourceId']}" 
            print(BedrockKBID)
    
        if "AWS::Bedrock::DataSource"==values['ResourceType']:
            dataSourceId=f"{values['PhysicalResourceId']}" 
            dataSourceId=dataSourceId.split("|")[1]
            print(dataSourceId)

        if "AWS::Cognito::UserPool"==values['ResourceType']:
            userpoolid=f"{values['PhysicalResourceId']}" 
            print(userpoolid)

        if "AWS::CloudFront::Distribution"==values['ResourceType']:

                # Get CloudFront client
                cloudfront_client = boto3.client('cloudfront')
                CF_PhysicalResourceId=f"{values['PhysicalResourceId']}" 
                dist_response = cloudfront_client.get_distribution(
                    Id=CF_PhysicalResourceId
                )
                DomainName=dist_response['Distribution']['DomainName']
                print(DomainName)


    return api_url,BedrockKBID,dataSourceId,userpoolid,DomainName


def loadsampledata(api_url,BedrockKBID):
    dynamodb_client = boto3.resource('dynamodb')
    DDBtableFM_table = dynamodb_client.Table(DDBtableFM)
    DDBtableFM_data=[
            {"Active":"amazon-nova-pro",
             "Image_Combine_prompt":"Summarize the Analaysis from these into 4-5 sentences",
             "Image_prompt":"You are an expert auto insurance investigator analyzing a claim image. FIRST, carefully examine the image to identify the exact vehicle make and model by checking the manufacturer's logo/emblem (on grille, back, or steering wheel), model badges, distinctive grille design, and body characteristics. This is a reported Car Make Model - if you observe ANY other manufacturer's logo or model, STOP immediately and report: 'CRITICAL MISMATCH: Image shows [actual vehicle observed] but reported vehicle is Car Make and Model.' Only proceed with further analysis if the vehicle identity is confirmed. If vehicle identity matches, provide a response starting with 'Based on the image uploaded, the car appears to be...' followed by your identification reasoning. Then conduct a detailed damage assessment examining front, back, top, and side areas. Describe the impact and damage in 3-4 clear sentences. Provide estimated repair costs and required labor based on provided parts data. Always conclude with: 'This repair estimate is preliminary. Final costs will be determined after detailed expert analysis.’",
             "knowledgeBaseId":BedrockKBID,
             "model_id":"amazon.nova-pro-v1:0",
             "region_id":region_name,
             "Summary_prompt": "Using the Combined_vehicle_image_analysis_output and data the knowledgebase detailing the potential cost to repair, generate an estimate to repair or replace the vehicle parts impacted including the potential labor. If possible provide the break down cost and final estimated cost including labor. Always call out at the end If the Make and Model of vehicle images and vehicle cost data given are not matching",
             "api_url":api_url} ,    
            {"Active":"Y",
             "Image_Combine_prompt":"Summarize the Analaysis from these into 4-5 sentences",
             "Image_prompt":"You are an expert auto insurance investigator analyzing a claim image. FIRST, carefully examine the image to identify the exact vehicle make and model by checking the manufacturer's logo/emblem (on grille, back, or steering wheel), model badges, distinctive grille design, and body characteristics. This is a reported Car Make Model - if you observe ANY other manufacturer's logo or model, STOP immediately and report: 'CRITICAL MISMATCH: Image shows [actual vehicle observed] but reported vehicle is Car Make and Model.' Only proceed with further analysis if the vehicle identity is confirmed. If vehicle identity matches, provide a response starting with 'Based on the image uploaded, the car appears to be...' followed by your identification reasoning. Then conduct a detailed damage assessment examining front, back, top, and side areas. Describe the impact and damage in 3-4 clear sentences. Provide estimated repair costs and required labor based on provided parts data. Always conclude with: 'This repair estimate is preliminary. Final costs will be determined after detailed expert analysis.’",
             "knowledgeBaseId":BedrockKBID,
             "model_id":"amazon.nova-pro-v1:0",
             "region_id":region_name,
             "Summary_prompt": "Using the Combined_vehicle_image_analysis_output and data the knowledgebase detailing the potential cost to repair, generate an estimate to repair or replace the vehicle parts impacted including the potential labor. If possible provide the break down cost and final estimated cost including labor. Always call out at the end If the Make and Model of vehicle images and vehicle cost data given are not matching",
             "api_url":api_url} ,      
]
    for item in DDBtableFM_data:
        DDBtableFM_table.put_item(Item=item)
        
    DDBtableVehiclePricing_table = dynamodb_client.Table(DDBtableVehiclePricing)
    DDBtableVehiclePricing_data=[
        {"CarMake_Model":"Toyota Camry 2021","Brakes":"300","Bumper":"400","Door":"700","Engine": "3500","Fender": "900","Headlight":"800","Suspension":"3000","Tires": "1500","Transmission":"4000","Windshield": "1250"},
        {"CarMake_Model":"Honda Accord 2014","Brakes":"200","Bumper":"300","Door":"800","Engine": "3000","Fender": "800","Headlight":"1000","Suspension":"2000","Tires": "2000","Transmission":"3000","Windshield": "1050"},
        {"CarMake_Model":"Tesla Model Y 2023","Brakes":"400","Bumper":"500","Door":"1000","Engine": "2000","Fender": "200","Headlight":"1400","Suspension":"3000","Tires": "1000","Transmission":"3000","Windshield": "1050"}
        ]
    for item in DDBtableVehiclePricing_data:
        DDBtableVehiclePricing_table.put_item(Item=item)
            
    DDBtableCustomerInfo_table = dynamodb_client.Table(DDBtableCustomerInfo)
    DDBtableCustomerInfo_data=[
        {"Policy_VIN":"PY1234","CustomerEmail": "mariag@example.com","CustomerName":"Maria Garcia","CustomerPhone":CustomerPhone,"Vehicles": ["Honda Accord 2014","Toyota Camry 2021"],"External_Id":"a27b7002-b383-434a-ba53-b451ef530a12","External_PolicyId":SOCOTRA_External_PolicyHolderId1},
        {"Policy_VIN":"PY0001","CustomerEmail": "mariag@example.com","CustomerName":"Maria Garcia","CustomerPhone":CustomerPhone,"Vehicles": ["Honda Accord 2014","Toyota Camry 2021"],"External_Id":"4db56456-fe6f-425c-a026-dfdb132d2f2b","External_PolicyId":SOCOTRA_External_PolicyHolderId2},
        {"Policy_VIN":"PY4321","CustomerEmail": "johndoe@example.com","CustomerName":"John Doe","CustomerPhone":CustomerPhone,"Vehicles": ["Honda Accord 2014","Toyota Camry 2021"],"External_Id":"78b883a0-72e2-4949-811f-06fe6fba5f34","External_PolicyId":SOCOTRA_External_PolicyHolderId3},
        {"Policy_VIN":"PY4000","CustomerEmail": "johndoe@example.com","CustomerName":"John Doe","CustomerPhone":CustomerPhone,"Vehicles": ["Honda Accord 2014","Toyota Camry 2021"],"External_Id":"f483c037-e2f9-450c-89d7-23362b603d1a","External_PolicyId":SOCOTRA_External_PolicyHolderId4},
        ]
    for item in DDBtableCustomerInfo_data:
        DDBtableCustomerInfo_table.put_item(Item=item)

    DDBtableNewClaim_table = dynamodb_client.Table(DDBtableNewClaim)
    DDBtableNewClaim_data=[
{
  "CaseNumber": "PY1234-123450",
  "CarMake_Model": "Toyota Camry 2021",
  "case_status": "New",
  "Combined_vehicle_image_analysis_output": "Test",
  "CustomerEmail": "Sample1@example.com",
  "CustomerName": "Sample1",
  "CustomerPhone": "+11234567891",
  "GenAI_Summary": "Test",
  "LossDate": "01-02-2025 14:30:00",
  "Vehicles": "Honda Accord 2014,Toyota Camry 2021",
  "LossLocation": "12346",
  "VehiclceAnalysis": {
  "vehicle1ToyotaCamry5": {"s3://bucket/upload/PY1234-123450/Sample1.jpeg": "Test"},
  "vehicle1ToyotaCamry1": {"s3://bucket/upload/PY1234-123450/Sample1.jpeg": "Test"},
  }
  },
{
  "CaseNumber": "PY1234-123451",
  "CarMake_Model": "Toyota Camry 2021",
  "case_status": "New",
  "Combined_vehicle_image_analysis_output": "Test",
  "CustomerEmail": "Sample2@example.com",
  "CustomerName": "Sample2",
  "CustomerPhone": "+11234567891",
  "GenAI_Summary": "Test",
  "LossDate": "01-02-2025 14:30:00",
  "Vehicles": "Honda Accord 2014,Toyota Camry 2021",
  "LossLocation": "12346",
  "VehiclceAnalysis": {
  "vehicle1ToyotaCamry5": {"s3://bucket/upload/PY1234-123451/Sample2.jpeg": "Test"},
  "vehicle1ToyotaCamry1": {"s3://bucket/upload/PY1234-123451/Sample2.jpeg": "Test"},
  }
  },
    ]
    for item in DDBtableNewClaim_data:
        response=DDBtableNewClaim_table.put_item(Item=item)
        print(response)

def interactive_sleep(seconds: int):
    dots = ''
    for i in range(seconds):
        dots += '.'
        print(dots, end='\r')
        time.sleep(1)


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

def ingestion (BedrockKBID,dataSourceId):
    # Start an ingestion job
    interactive_sleep(30)
    start_job_response = bedrock_agent_client.start_ingestion_job(knowledgeBaseId = BedrockKBID, dataSourceId = dataSourceId)
    job = start_job_response["ingestionJob"]
    pp.pprint(job)
    # Get job 
    while(job['status']!='COMPLETE' ):
        get_job_response = bedrock_agent_client.get_ingestion_job(
        knowledgeBaseId = BedrockKBID,
        dataSourceId = dataSourceId,
        ingestionJobId = job["ingestionJobId"]
        )
        job = get_job_response["ingestionJob"]
        
        interactive_sleep(30)
        pp.pprint(job)

def upload(filepath):
    upload_url_response = lex_client.create_upload_url()
    #print(upload_url_response)
    upload_url = upload_url_response['uploadUrl']
    print(upload_url)
    importId = upload_url_response['importId']
    print(importId)
    # Upload the bot archive to the pre-signed S3 URL
    # Replace 'bot_archive.zip' with the actual path to your bot archive file
    
    with open(filepath, "rb") as file:
            file_data = file.read()
            s3_client = boto3.client('s3')
            response = requests.put(upload_url, data=file_data)
        
    # Start the import process
    import_summary = lex_client.start_import(
        importId=importId,  # Replace with a unique import ID
        resourceSpecification={
            'botImportSpecification': {
                'botName': 'GP-FSI-Claims-Processing',            
                'roleArn': f'arn:aws:iam::{account_id}:role/gp-fsi-claims-processing-lex-role',
                'dataPrivacy': {
                    'childDirected': False
                },
            }
        },
        mergeStrategy='Overwrite'  # Specify the merge strategy ('Overwrite' or 'Fail')
    )
    #print(import_summary)
    #status = import_summary['importStatus']
    return importId
    
def build(importId) : 
    status=""
    print("Checking Import status")
    while(status!='Completed' ):
        response = lex_client.describe_import(
        importId=importId
        )
        status=response['importStatus']
        interactive_sleep(2)
        print(status)
    
    

    botid=response['importedResourceId']
    print("Bot imported successfully")
    print(botid)
    
   # interactive_sleep(10)
    
    response = lex_client.build_bot_locale(
        botId=botid,
        botVersion='DRAFT',
        localeId='en_US'
    )
    print("Checking Build status")
    while(status!='Built' ):
        response = lex_client.describe_bot_locale(
        botId=botid,
        botVersion='DRAFT',
        localeId='en_US'
        )
        status=response['botLocaleStatus']
        interactive_sleep(10)
        print(status)
    print("Bot Built successfully")
    return botid

def update_alias(botid):
    botAliasId='TSTALIASID'
    response = lex_client.update_bot_alias(
    botAliasId=botAliasId,
    botAliasName='TestBotAlias',
    description='TestBotAlias',
    botVersion='DRAFT',
    botAliasLocaleSettings={
        'en_US': {
            'enabled': True,
            'codeHookSpecification': {
                'lambdaCodeHook': {
                'lambdaARN': f'arn:aws:lambda:{region_name}:{account_id}:function:gp-fsi-claimprocessing-filenewclaim',
                'codeHookInterfaceVersion': '1.0'
                }
            }
        }
    },    
    botId=botid
    )
    print(response)
    return botid,botAliasId

def update_bucket_cors(bucket_name, domain):
    """
    Update the CORS configuration of an S3 bucket
    
    Args:
        bucket_name (str): Name of the S3 bucket
        domain (str): Domain to allow in CORS (e.g., CloudFront domain)
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Define CORS configuration
        cors_configuration = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': [f'https://{domain}'
                                   ,'http://localhost:3000' # for ttesting from local. You can remove it if needed.
                                   ],
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }]
        }

        # Apply CORS configuration to bucket
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        
        print(f"Successfully updated CORS configuration for bucket: {bucket_name}")
        print(f"Allowed origin: https://{domain}")
        
        # Verify the configuration
        cors_config = s3_client.get_bucket_cors(Bucket=bucket_name)
        print("\nCurrent CORS Configuration:")
        print(cors_config)
        
    except Exception as e:
        print(f"Error updating CORS configuration: {str(e)}")


def main():
    api_url,BedrockKBID,dataSourceId,userpoolid,DomainName=getAPIInfo()
    print("Updating S3 Cors")
    update_bucket_cors(bucket_name, DomainName)
    print("Updated S3 Cors")
    print("Uploading sample files for Bedrock Knowledge base S3")
    upload_directory_to_s3(local_directory, bucket_name, s3_prefix)
    print("Running the Bedrock Knowledge base Sync job")
    ingestion (BedrockKBID,dataSourceId)
    print("Completed the Bedrock Knowledge base Sync job")
    print("Loading sample data to the Dynamodb table")
    loadsampledata(api_url,BedrockKBID)
    print("Completed loading sample data to the Dynamodb table")
    print("Creating a sample user")
    username="test"
    email="test@example.com"
    temporary_password="Test@1234"
    create_cognito_user(userpoolid, username, email, temporary_password)  
    print("Importing Sample Lex chatbot")
    filepath=os.getcwd()+"/Amazon Lex/GP-FSI-Claims-Processing.zip"
    print(filepath)
    importId=upload(filepath)
    botid=build(importId)
    botid,botAliasId=update_alias(botid)
    print(botid,botAliasId)
    
main ()