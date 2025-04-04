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

#!/bin/bash

# Function to cleanup EIPs
cleanup_eips() {
    echo "Cleaning up Elastic IPs..."
    
    # Get all EIPs created by the stack
    EIPS=$(aws cloudformation list-stack-resources \
        --stack-name ClaimsProcessingStack1 \
        --query "StackResourceSummaries[?ResourceType=='AWS::EC2::EIP'].PhysicalResourceId" \
        --output text 2>/dev/null) || true
    
    if [ -n "$EIPS" ]; then
        for eip in $EIPS; do
            echo "Attempting to release EIP: $eip"
            aws ec2 release-address --allocation-id "$eip" 2>/dev/null || true
            sleep 1
        done
    fi
    echo "EIP cleanup attempted"
}

# Function to cleanup Network Interfaces
cleanup_enis() {
    echo "Cleaning up Network Interfaces..."
    
    # Get all ENIs created by the stack
    ENIS=$(aws cloudformation list-stack-resources \
        --stack-name ClaimsProcessingStack1 \
        --query "StackResourceSummaries[?ResourceType=='AWS::EC2::NetworkInterface'].PhysicalResourceId" \
        --output text 2>/dev/null) || true
    
    if [ -n "$ENIS" ]; then
        for eni in $ENIS; do
            echo "Processing ENI: $eni"
            
            # Attempt to detach and delete without stopping on errors
            ATTACHMENT_ID=$(aws ec2 describe-network-interfaces \
                --network-interface-ids "$eni" \
                --query 'NetworkInterfaces[0].Attachment.AttachmentId' \
                --output text 2>/dev/null) || true
            
            if [ "$ATTACHMENT_ID" != "None" ] && [ -n "$ATTACHMENT_ID" ]; then
                aws ec2 detach-network-interface \
                    --attachment-id "$ATTACHMENT_ID" \
                    --force 2>/dev/null || true
                sleep 2
            fi
            
            aws ec2 delete-network-interface --network-interface-id "$eni" 2>/dev/null || true
            sleep 1
        done
    fi
    echo "Network Interface cleanup attempted"
}

# Find and delete the Lex bot
cleanup_lexbot() {
    echo "Cleaning up Lex bot..."
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
}

# Main cleanup function
cleanup_all() {
    echo "Starting cleanup process..."
    
    # Run all cleanups without stopping on errors
    cleanup_eips
    cleanup_enis
    cleanup_lexbot
    
    # Short wait before stack deletion
    sleep 5
    
    # Destroy the stack without confirmation
    echo "Attempting to destroy CloudFormation stack..."
    cdk destroy ClaimsProcessingStack1
    
    echo "Cleanup process completed"
}

# Execute cleanup
cleanup_all

