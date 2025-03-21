#excample usage:
#./destroy.sh us-east-1

# Check if region parameter is provided
if [ $# -eq 0 ]; then
    echo "No region specified. Usage: ./destroy.sh <region-name>"
    echo "Example: ./destroy.sh us-east-1"
    exit 1
fi

export AWS_REGION="$1"

path="$PWD/source/"
echo $path
cd $path

# Install requirements
#python3 -m venv myvenv
python3 -m venv /tmp/.venv
#source myvenv/bin/activate
source /tmp/.venv/bin/activate
pip install -r requirements.txt

export DDBtableNewClaim="GP-FSI-ClaimsProcessing-NewClaim"
export DDBtableFM="GP-FSI-ClaimsProcessing-FM"
export DDBtableVehiclePricing="GP-FSI-ClaimsProcessing-VehiclePricing"
export DDBtableCustomerInfo="GP-FSI-ClaimsProcessing-CustomerInfo"
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
export BedrockKBID="*******" 
export bucketname_input="gp-fsi-claims-processing"

# Find the bot ID for GP-FSI-Claims-Processing
BOT_ID=$(aws lexv2-models list-bots --query 'botSummaries[?botName==`GP-FSI-Claims-Processing`].botId' --output text)

if [ -n "$BOT_ID" ]; then
    echo "Found bot with ID: $BOT_ID"
    # Delete the bot
    aws lexv2-models delete-bot --bot-id "$BOT_ID" --skip-resource-in-use-check
    if [ $? -eq 0 ]; then
        echo "Successfully deleted bot: GP-FSI-Claims-Processing"
    else
        echo "Error deleting bot, manaully delete the chatbot"
    fi
else
    echo "No bot found with name: GP-FSI-Claims-Processing"
fi

cdk destroy ClaimsProcessingStack1
echo "Clean up completed"