import boto3
import os
import requests
import time

# Create a Lex client
account_id = boto3.client('sts').get_caller_identity().get('Account')



account_id = boto3.client('sts').get_caller_identity().get('Account')
identity = boto3.client('sts').get_caller_identity()['Arn']
s3_client = boto3.client('s3')
bucket_name = f'gp-fsi-claims-processing{account_id}' # replace it with your bucket name.
local_directory = "Knowledgebase/"
s3_prefix = "Knowledgebase/"

region_name = "us-east-1"  # default region

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


lex_client = boto3.client('lexv2-models')
client = boto3.client('lex-models')
# Create a pre-signed S3 URL to upload the bot archive
tagclient = boto3.client('resourcegroupstaggingapi')


def interactive_sleep(seconds: int):
    dots = ''
    for i in range(seconds):
        dots += '.'
        print(dots, end='\r')
        time.sleep(1)
    # print('Done!')
    
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
    
def main():
    filepath=os.getcwd()+"/Amazon Lex/GP-FSI-Claims-Processing.zip"
    print(filepath)
    importId=upload(filepath)
    botid=build(importId)
    botid,botAliasId=update_alias(botid)
    print(botid,botAliasId)

main()