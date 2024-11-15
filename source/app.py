import os
import aws_cdk as cdk
import boto3

from claimsprocessing.claimsprocessing import ClaimsProcessingStack1
from claimsprocessing.claimsprocessing import ClaimsProcessingStack2
from claimsprocessing.claimsprocessing import ClaimsProcessingStack3
from claimsprocessing.claimsprocessing import ClaimsProcessingStack4

stack_variables={}
stack_variables['DDBtableNewClaim']=os.getenv("DDBtableNewClaim"),
stack_variables['DDBtableFM']=os.getenv("DDBtableFM"),
stack_variables['DDBtableVehiclePricing']=os.getenv("DDBtableVehiclePricing"),
stack_variables['DDBtableCustomerInfo']=os.getenv("DDBtableCustomerInfo"),
stack_variables['Pinpoint_app_id']=os.getenv("Pinpoint_app_id"), 
stack_variables['Pinpoint_origination_number']=os.getenv("Pinpoint_origination_number")
#print(os.getenv("BedrockKBID"))
stack_variables['BedrockKBID']=os.getenv("BedrockKBID")
stack_variables['bucketname_input']=os.getenv("bucketname_input")


app = cdk.App()

ClaimsProcessingStack1=ClaimsProcessingStack1(app, "ClaimsProcessingStack1",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    stack_variables=stack_variables
    )
    
ClaimsProcessingStack2=ClaimsProcessingStack2(app, "ClaimsProcessingStack2",
    ClaimsProcessingStack1=ClaimsProcessingStack1
    )
    
ClaimsProcessingStack3=ClaimsProcessingStack3(app, "ClaimsProcessingStack3",
    ClaimsProcessingStack1=ClaimsProcessingStack1
    )
    
ClaimsProcessingStack4=ClaimsProcessingStack4(app, "ClaimsProcessingStack4",
    ClaimsProcessingStack1=ClaimsProcessingStack1
    )
    
app.synth()
