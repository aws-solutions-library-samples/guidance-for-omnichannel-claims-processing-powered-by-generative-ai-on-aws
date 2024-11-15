import os
import boto3
'''Load sample data to DynamoDB tables'''


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

DDBtableFM=os.environ['DDBtableFM']
DDBtableVehiclePricing=os.environ['DDBtableVehiclePricing']
DDBtableCustomerInfo=os.environ['DDBtableCustomerInfo']
BedrockKBID=os.environ['BedrockKBID']
DDBtableNewClaim=os.environ['DDBtableNewClaim']

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
            api_url=f"https://{values['PhysicalResourceId']}.execute-api.us-east-1.amazonaws.com/dev/lambda" 
            print(api_url)
            return api_url


def loadsampledata(api_url):
    dynamodb_client = boto3.resource('dynamodb')
    DDBtableFM_table = dynamodb_client.Table(DDBtableFM)
    DDBtableFM_data=[
            {"Active":"Y","Image_Combine_prompt":"Summarize the Analaysis from these into 4-5 sentences","Image_prompt":"The given image is from an auto insurance claim. You are an expert auto insurance investigator with expertise in identifying make,model and color of car and infer the extent of damage to the car from the pictures. Make and model of the car can be detected by looking at the logo or emblem on the front grille, back or steering wheel. Detect and summarize the make, model and color of the car by looking at the image and call out if you see discrepencies between what you detected vs what is reported by the customer. Also summarize the damages to the car by looking at the front, back, top and side of the car. Ignore any aspects around the background. Articulate the impact of damages in detail and areas of damage and summarize it in 3-4 sentences. Include potential cost to repair and the labor involved using the sample vehicle parts data given. Always mention the repair estimate is just an indication and the final estimate will be provided based on further analysis by our experts. Start the output like the below:Based on the image uploaded , the car appears to be .... Explain why you think the car appears to be.... Specifically call out if the make of the car is different from what the customer reported when submitting a claim. Clearly indicate additional analysis by experts is needed to verify accuracy","knowledgeBaseId":BedrockKBID,"model_id":"anthropic.claude-3-haiku-20240307-v1:0","region_id":region_name,"Summary_prompt": "Using the Combined_vehicle_image_analysis_output and data the knowledgebase detailing the potential cost to repair, generate an estimate to repair or replace the vehicle parts impacted including the potential labor. If possible provide the break down cost and final estimated cost including labor. Always call out at the end If the Make and Model of vehicle images and vehicle cost data given are not matching","api_url":api_url}      
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
        {"Policy_VIN":"PY1234","CustomerEmail": "mariag@example.com","CustomerName":"Maria Garcia","CustomerPhone":"+1234567890","Vehicles": ["Honda Accord 2014","Toyota Camry 2021"]}
        ]
    for item in DDBtableCustomerInfo_data:
        DDBtableCustomerInfo_table.put_item(Item=item)

    DDBtableNewClaim_table = dynamodb_client.Table(DDBtableNewClaim)
    DDBtableNewClaim_data=[
    {"CaseNumber":"PY1234-123456"},
    {"CaseNumber":"PY1234-123457"},
    {"CaseNumber":"PY1234-123458"},
    {"CaseNumber":"PY1234-123459","CarMake_Model":"Honda Accord 2014","case_status":"Review","Combined_vehicle_image_analysis_output":"The vehicle image results provided contain analyses of two separate vehicles, a Toyota Camry and a Honda Accord, that were involved in significant accidents. The analysis for the Toyota Camry indicates that the front end of the vehicle sustained severe damage, including a crushed bumper, grille, and hood, as well as a shattered windshield and damage to the fender and wheel well. This suggests a high-impact collision that has rendered the vehicle inoperable and in need of extensive repairs or replacement.\n\nThe analysis for the Honda Accord also describes significant damage to the front end of the vehicle, including a crumpled hood, damaged front bumper, and heavily impacted headlights. The extent of the damage suggests a high-speed collision or a collision with a larger vehicle. The analysis indicates that the front end of the vehicle has been severely compromised and would require extensive repairs to restore the vehicle to its pre-accident condition.\n\nWhile the two vehicles appear to be different models, the analyses provided show that both vehicles sustained significant front-end damage, indicating they were likely involved in separate high-impact collisions. The detailed descriptions of the damage to each vehicle suggest that the claims processing team has a clear understanding of the extent of the damage and the necessary repairs required.","CustomerEmail":"gMaria@example.com","CustomerName":"GARCIA Maria","CustomerPhone":"+11234567890","GenAI_Summary":"Based on the detailed vehicle image analysis provided and the vehicle data given, it appears that the two vehicles involved in the accidents were a Toyota Camry and a Honda Accord, not a single Honda Accord as indicated in the vehicle data. The vehicle data provided does not match the information in the image analysis, so I cannot provide a complete repair estimate for the vehicle.","LossDate":"", "LossLocation":""},
        ]
    for item in DDBtableNewClaim_data:
        response=DDBtableNewClaim_table.put_item(Item=item)
        print(response)
    

def main():
    api_url=getAPIInfo()
    loadsampledata(api_url)
    
    
main ()