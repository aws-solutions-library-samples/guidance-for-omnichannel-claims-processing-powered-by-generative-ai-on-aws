path="$PWD/source/"
echo $path
cd $path

#ui_update=$path"/claimsuidockerapp/Sample/Config.py"
#echo $ui_update

# Install requirements
#python3 -m venv myvenv
python3 -m venv /tmp/.venv
#source myvenv/bin/activate
source /tmp/.venv/bin/activate
python -m pip install --upgrade pip
#echo $PWD
pip install -r requirements.txt

export DDBtableNewClaim="GP-FSI-ClaimsProcessing-NewClaim"
export DDBtableFM="GP-FSI-ClaimsProcessing-FM"
export DDBtableVehiclePricing="GP-FSI-ClaimsProcessing-VehiclePricing"
export DDBtableCustomerInfo="GP-FSI-ClaimsProcessing-CustomerInfo"
export Pinpoint_app_id="xxxxxxxxxx" #change it
export Pinpoint_origination_number="+1234567890" #change it
#echo $DDBtableNewClaim
#echo $DDBtableFM
export BedrockKBID="" #Fill this if you already have a knowledge base
export bucketname_input="gp-fsi-claims-processing"

# Bootstrap CDK if you have not done so before
#cdk bootstrap
cdk init
cdk bootstrap
# Run CDK deploy
cdk synth ClaimsProcessingStack1 
echo "Deploying stack1"
cdk deploy ClaimsProcessingStack1

cdk synth ClaimsProcessingStack2
echo "Deploying ClaimsProcessingStack2"
cdk deploy ClaimsProcessingStack2

cdk synth ClaimsProcessingStack3
echo "Deploying stack3"
cdk deploy ClaimsProcessingStack3


cdk synth ClaimsProcessingStack4
echo "Deploying stack4"
cdk deploy ClaimsProcessingStack4

echo "Running loadsampledata.py to load sample data to dynamodb tables"
python "$PWD/claimsprocessing/loadsampledata.py"

echo "Running setup_AmazonBedrock_kb.py to set up knowldge base"
python "$PWD/claimsprocessing/setup_AmazonBedrock_kb.py"


echo "Running LexImport.py to set up Amazon Lex"
python "$PWD/claimsprocessing/LexImport.py"