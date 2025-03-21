import os
import aws_cdk as cdk
import boto3

from claimsprocessing.claimsprocessing import ClaimsProcessingStack1
#from claimsprocessing.claimsprocessing import ClaimsProcessingStack2


# from aws_cdk import App, Aspects
# from cdk_nag import AwsSolutionsChecks, NagSuppressions

stack_variables={}
stack_variables['DDBtableNewClaim']=os.getenv("DDBtableNewClaim"),
stack_variables['DDBtableFM']=os.getenv("DDBtableFM"),
stack_variables['DDBtableVehiclePricing']=os.getenv("DDBtableVehiclePricing"),
stack_variables['DDBtableCustomerInfo']=os.getenv("DDBtableCustomerInfo"),
stack_variables['SMS_Origination_number_ARN']=os.getenv("SMS_Origination_number_ARN")
#print(os.getenv("BedrockKBID"))
stack_variables['BedrockKBID']=os.getenv("BedrockKBID")
stack_variables['bucketname_input']=os.getenv("bucketname_input")
stack_variables['reactpath']=os.getenv("reactpath")
stack_variables['SOCOTRA_ENDPOINT']=os.getenv("SOCOTRA_ENDPOINT")
stack_variables['SOCOTRA_HOST']=os.getenv("SOCOTRA_HOST")
stack_variables['SOCOTRA_USERNAME']=os.getenv("SOCOTRA_USERNAME")
stack_variables['SOCOTRA_PASSWORD']=os.getenv("SOCOTRA_PASSWORD")
stack_variables['execution']=os.getenv("execution")
stack_variables['GW_USERNAME']=os.getenv("GW_USERNAME")
stack_variables['GW_PASSWORD']=os.getenv("GW_PASSWORD")
stack_variables['GW_BASE_URL']=os.getenv("GW_BASE_URL")


app = cdk.App()


ClaimsProcessingStack1=ClaimsProcessingStack1(app, "ClaimsProcessingStack1",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    stack_variables=stack_variables
    )

# ClaimsProcessingStack2=ClaimsProcessingStack2(app, "ClaimsProcessingStack2",
#     ClaimsProcessingStack1=ClaimsProcessingStack1
#     )

# # Add the AWS Solutions checks to the entire app
# Aspects.of(app).add(AwsSolutionsChecks())

app.synth()


