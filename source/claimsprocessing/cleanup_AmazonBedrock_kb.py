import boto3
import os

boto3_session = boto3.session.Session()

iam_client = boto3_session.client('iam')
account_id = boto3.client('sts').get_caller_identity().get('Account')
identity = boto3.client('sts').get_caller_identity()['Arn']
s3_client = boto3.client('s3')
bucket_name = f'gp-fsi-claims-processing{account_id}' # replace it with your bucket name.
local_directory = "Knowledgebase/"
s3_prefix = "Knowledgebase/"

'''
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
'''
region_name = os.environ.get('AWS_REGION', 'us-east-1')

print(f"Identity: {identity}")
print(f"Account ID: {account_id}")
print(f"Region: {region_name}")

os.environ['AWS_DEFAULT_REGION'] = region_name

aoss_client=boto3.client('opensearchserverless')
bedrock_client = boto3.client('bedrock-agent')

        
response = aoss_client.list_collections(
    collectionFilters={
        'status': 'ACTIVE'
    },
)

for collection in response['collectionSummaries']:
     if "gp-fsi-claims-processing" in collection['name']:
        print(collection['id'])
        response = aoss_client.delete_collection(
            id=collection['id']
            )
        print(response)


def clean_policy(PolicyArn):
    try:
        response = iam_client.delete_policy(
        PolicyArn=PolicyArn
        )
    except:
        pass
    

def del_role(RoleName):
    print(RoleName)
    list=["AmazonBedrockFoundationModelPolicyForKB_gp_fsi_claimsprocessing","AmazonBedrockOSSPolicyForKB_gp_fsi_claimsprocessing" ,"AmazonBedrockS3PolicyForKB_gp_fsi_claimsprocessing"]
    for item in list:
        suffix=RoleName.split("gp_fsi_claimsprocessing_")[1]
        PolicyArn=f"arn:aws:iam::{account_id}:policy/{item}_{suffix}"
        print(PolicyArn)
        try:
            response = iam_client.detach_role_policy(
            RoleName=RoleName,
            PolicyArn=PolicyArn
            )
            #print(response)
        except:
            pass
    
    response = iam_client.delete_role(RoleName=RoleName)
  
response = iam_client.list_roles()
for role in response['Roles']:
    if 'AmazonBedrockExeRoleforKB_gp_fsi_claimsprocessing_' in role['RoleName']:
        print(role['RoleName'])
        print(role['Arn'])
        del_role(role['RoleName'])
        
response = iam_client.list_policies(
    Scope='Local'
)
for policy in response['Policies']:
    if "AmazonBedrockFoundationModelPolicyForKnowledgeBase" in policy['PolicyName'] or "AmazonBedrockFoundationModelPolicyForKB_gp_fsi_claimsprocessing" in policy['PolicyName'] or "AmazonBedrockOSSPolicyForKB_gp_fsi_claimsprocessing_" in policy['PolicyName'] or "AmazonBedrockS3PolicyForKB_gp_fsi_claimsprocessing_" in policy['PolicyName'] :
        print(policy['PolicyName'])
        print(policy['Arn'])
        clean_policy(policy['Arn'])
        
        
def cleanup(item,ptype):
    try:
        response = aoss_client.delete_security_policy(
        name=item,
        type=ptype
        )
    except:
        pass
    
response = aoss_client.list_access_policies(
    type='data'
)
#print(response)
for accesspolicy in response['accessPolicySummaries']:
    if "gp-fsi-claims-processing" in accesspolicy['name']:
        print(accesspolicy['name'])
        print(accesspolicy['type'])
        #cleanup(accesspolicy['name'],accesspolicy['type']) -- Not supported today
        os.system("aws opensearchserverless  delete-access-policy --name "+accesspolicy['name']+" --type data")



response = aoss_client.list_security_policies(
    type='encryption'
)
for secpolicy in response['securityPolicySummaries']:
    if "gp-fsi-claims-processing" in secpolicy['name']:
        print(secpolicy['name'])
        print(secpolicy['type'])
        cleanup(secpolicy['name'],secpolicy['type'])
        
        
response = aoss_client.list_security_policies(
    type='network'
)
for secpolicy in response['securityPolicySummaries']:
    if "gp-fsi-claims-processing" in secpolicy['name']:
        print(secpolicy['name'])
        print(secpolicy['type'])
        cleanup(secpolicy['name'],secpolicy['type'])


response = bedrock_client.list_knowledge_bases()
for kbs in response['knowledgeBaseSummaries']:
    if "gp-fsi-claims-processing-knowledge-base" in kbs['name']:
        print(kbs['name'])
        print(kbs['knowledgeBaseId'])
        response = bedrock_client.delete_knowledge_base(
        knowledgeBaseId=kbs['knowledgeBaseId']
        )
        
print("Bedrock resource clean up completed")