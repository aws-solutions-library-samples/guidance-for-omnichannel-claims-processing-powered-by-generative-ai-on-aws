#!/bin/bash
set -e  # Exit on error

# Check if region parameter is provided
if [ $# -eq 0 ]; then
    echo "No region specified. Usage: ./deploy.sh <region-name>"
    echo "Example: ./deploy.sh us-east-1"
    echo "Example: sh deploy.sh us-east-1"
    exit 1
fi

export AWS_REGION="$1"
AWS_REGION="$1"

sourcepath="$PWD/source"
echo $sourcepath
reactpath="$sourcepath/ReactApp"
echo $reactpath

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=true

cd $sourcepath

# First, remove any existing virtual environment
rm -rf /tmp/.venv

# Create a new virtual environment
python3 -m venv /tmp/.venv

# Activate the virtual environment
source /tmp/.venv/bin/activate

# Install dependencies within the virtual environment
python3 -m pip install --upgrade pip
pip install publication
pip install -r requirements.txt
pip install aws-cdk-lib constructs


# Set environment variables
export DDBtableNewClaim="GP-FSI-ClaimsProcessing-NewClaim"
export DDBtableFM="GP-FSI-ClaimsProcessing-FM"
export DDBtableVehiclePricing="GP-FSI-ClaimsProcessing-VehiclePricing"
export DDBtableCustomerInfo="GP-FSI-ClaimsProcessing-CustomerInfo"
export BedrockKBID="" #Fill this if you already have a knowledge base
export bucketname_input="gp-fsi-claims-processing"
export reactpath="$reactpath"

#export CustomerPhone="+12341231234" #change it
export SOCOTRA_External_PolicyHolderId1="899124618"
export SOCOTRA_External_PolicyHolderId2="963201198"
export SOCOTRA_External_PolicyHolderId3="401046625"
export SOCOTRA_External_PolicyHolderId4="333426651"


export SOCOTRA_ENDPOINT="XXX"
export SOCOTRA_HOST="XXX"
export SOCOTRA_USERNAME="XXX"
export SOCOTRA_PASSWORD="XXX"
export REACT_APP_STRIPE_PUBLISH_KEY="XXX"
export GW_USERNAME="XXX"
export GW_PASSWORD="XXX"
export GW_BASE_URL="XXX"
export SMS_Origination_number_ARN="XXX"
export CustomerPhone="XXX"



# Bootstrap CDK if you have not done so before
cdk init
cdk bootstrap
# Run CDK deploy
cdk synth ClaimsProcessingStack1 
echo "Deploying stack1"
cdk deploy ClaimsProcessingStack1 --require-approval never

#exit 1

cd $reactpath
# # Set your AWS region
# AWS_REGION="us-east-1"

# Path prefix for SSM parameters
SSM_PATH="/GP-FSI-ClaimsProcessing"

# Output file

# Function to get SSM parameter
get_ssm_parameter() {
    aws ssm get-parameter --name "$1" --region $AWS_REGION --query "Parameter.Value" --output text
}
# Create or clear the .env file

touch .env
ENV_FILE=.env
# Get and write parameters to .env file
echo "Fetching SSM parameters and writing to .env file..."

# AWS Region
echo "REACT_APP_AWS_REGION=$AWS_REGION" > $ENV_FILE

# Add AWS account ID to env file
AWS_ACCOUNT_ID=$(get_ssm_parameter "$SSM_PATH/AWS_ACCOUNT_ID")
echo "REACT_APP_AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID" >> $ENV_FILE

# Fetch and write other parameters
echo "REACT_APP_COGNITO_USER_POOL_ID=$(get_ssm_parameter "$SSM_PATH/COGNITO_USER_POOL_ID")" >> $ENV_FILE
echo "REACT_APP_COGNITO_CLIENT_ID=$(get_ssm_parameter "$SSM_PATH/COGNITO_CLIENT_ID")" >> $ENV_FILE
echo "REACT_APP_IDENTITY_POOL_ID=$(get_ssm_parameter "$SSM_PATH/REACT_APP_IDENTITY_POOL_ID")" >> $ENV_FILE
echo "REACT_APP_DDBTableNameClaim=$(get_ssm_parameter "$SSM_PATH/DDBTableNameClaim")" >> $ENV_FILE
echo "REACT_APP_DDBTableNameCustomer=$(get_ssm_parameter "$SSM_PATH/DDBTableNameCustomer")" >> $ENV_FILE
echo "REACT_APP_S3BUCKET=$(get_ssm_parameter "$SSM_PATH/REACT_APP_S3BUCKET")" >> $ENV_FILE
echo "REACT_APP_NOTIFICATION_SQS_QUEUE_URL=$(get_ssm_parameter "$SSM_PATH/REACT_APP_NOTIFICATION_SQS_QUEUE_URL")" >> $ENV_FILE
echo "REACT_APP_3P_SQS_QUEUE_URL=$(get_ssm_parameter "$SSM_PATH/REACT_APP_3P_SQS_QUEUE_URL")" >> $ENV_FILE
echo "REACT_APP_DDBTableNameFM=$(get_ssm_parameter "$SSM_PATH/REACT_APP_DDBTableNameFM")" >> $ENV_FILE
echo "REACT_APP_REACTAPI=$(get_ssm_parameter "$SSM_PATH/REACT_APP_REACTAPI")" >> $ENV_FILE
echo "REACT_APP_3PAPI=$(get_ssm_parameter "$SSM_PATH/REACT_APP_3PAPI")" >> $ENV_FILE
echo "REACT_APP_3PAPI_SOCOTRA_ENDPOINT=$SOCOTRA_ENDPOINT" >> $ENV_FILE
echo "REACT_APP_3PAPI_SOCOTRA_HOST=$SOCOTRA_HOST" >> $ENV_FILE
echo "REACT_APP_3PAPI_SOCOTRA_UNAME=$SOCOTRA_USERNAME" >> $ENV_FILE
echo "REACT_APP_3PAPI_SOCOTRA_PASS=$SOCOTRA_PASSWORD" >> $ENV_FILE
echo "REACT_APP_STRIPE_PUBLISH_KEY=$REACT_APP_STRIPE_PUBLISH_KEY" >> $ENV_FILE
echo "REACT_APP_3PAPI_GW_USERNAME=$GW_USERNAME" >> $ENV_FILE
echo "REACT_APP_3PAPI_GW_PASSWORD=$GW_PASSWORD" >> $ENV_FILE
echo "REACT_APP_3PAPI_GW_BASE_URL=$GW_BASE_URL" >> $ENV_FILE

# Then append a line with date and time at the end of the file
echo -e "\n# Last updated on $(date '+%Y-%m-%d %H:%M:%S %Z')" >> $ENV_FILE


# Verify the file was created and has content
if [ -s "$ENV_FILE" ]; then
    echo "Successfully created .env file with SSM parameters"
else
    echo "Error: Failed to create .env file or file is empty"
    exit 1
fi

# Re-Build React app
echo "Re-Building React app..."
npm install -g react-scripts
npm install
npm run build



# Deploy the stack to accomodate the React App Env changes with the dynamic CDK resources values
export execution="second"
# Navigate to infrastructure directory
cd $sourcepath

# # Deploy the stack
# echo "Re-Deploying CDK stack to make sure the new ReactApp build files are uploaded..."
# cdk deploy ClaimsProcessingStack1 --require-approval never

# Activate the virtual environment
source /tmp/.venv/bin/activate
pip install requests
echo "Running loadsamples.py to load sample data to dynamodb tables and import the sample Amazon Lex chatbot and upload the react build files to S3"
python3 "$PWD/claimsprocessing/loadsamples.py"

