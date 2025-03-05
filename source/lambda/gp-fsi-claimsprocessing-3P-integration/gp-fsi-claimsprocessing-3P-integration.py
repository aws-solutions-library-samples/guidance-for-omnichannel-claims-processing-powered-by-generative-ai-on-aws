import json
import urllib3
import os
from datetime import datetime
import base64

# Disable SSL warnings - only for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Existing Socotra configurations
SOCOTRA_ENDPOINT = os.environ.get('SOCOTRA_ENDPOINT', 'https://api.sandbox.socotra.com')
SOCOTRA_HOST = os.environ.get('SOCOTRA_HOST')
SOCOTRA_USERNAME = os.environ.get('SOCOTRA_USERNAME')
SOCOTRA_PASSWORD = os.environ.get('SOCOTRA_PASSWORD')

# Guidewire configurations
GW_USERNAME = os.getenv('GW_USERNAME')  # Fallback to 'su' if not set
GW_PASSWORD = os.getenv('GW_PASSWORD')  # Fallback to 'gw' if not set
GW_BASE_URL = os.getenv('GW_BASE_URL')

def parse_guidewire_claims(claims_response):
    """Parse claims data from Guidewire response"""
    parsed_claims = []
    
    if not claims_response or 'data' not in claims_response:
        return parsed_claims
    
    for claim in claims_response['data']:
        if 'attributes' in claim:
            attrs = claim['attributes']
            parsed_claim = {
                'locator': attrs.get('claimId', 'N/A'),
                'currentStatus': attrs.get('status', {}).get('name', 'N/A'),
                'incident_type': 'Auto',  # Default to Auto for Guidewire claims
                'incident_summary': f"Claim handled by {attrs.get('adjusterName', 'Unknown')} - {attrs.get('assignedGroup', 'Unknown')}",
                'createdTimestamp': attrs.get('lossDate', 'N/A'),
                'policyLocator': attrs.get('policyNumber', 'N/A'),
                'claimNumber': attrs.get('claimNumber', 'N/A'),
                'adjusterName': attrs.get('adjusterName', 'N/A'),
                'paidAmount': attrs.get('paid', {}).get('amount', '0.00'),
                'insuredName': attrs.get('insuredName', 'N/A')
            }
            parsed_claims.append(parsed_claim)
    
    return parsed_claims

def get_guidewire_claims(http, policy_numbers):
    """Fetch claims from Guidewire for given policy numbers"""
    if not GW_BASE_URL:
        raise Exception("Guidewire API configuration missing")

    # Create basic auth header
    credentials = base64.b64encode(f"{GW_USERNAME}:{GW_PASSWORD}".encode()).decode()
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Basic {credentials}'
    }

    all_claims = []
    for policy_number in policy_numbers:
        print(policy_number)
        payload = {
            "data": {
                "attributes": {
                    "policyNumber": policy_number
                }
            }
        }
        print(json.dumps(payload))
        print(f"{GW_BASE_URL}/claim/v1/search/claims-v2")
        try:
            response = http.request(
                'POST',
                f"{GW_BASE_URL}/claim/v1/search/claims-v2",
                headers=headers,
                body=json.dumps(payload)
            )
            #print(response)
                
            claims_data = json.loads(response.data.decode('utf-8'))
            print(claims_data)
            parsed_claims = parse_guidewire_claims(claims_data)
            all_claims.extend(parsed_claims)
            print(f"Successfully processed {len(parsed_claims)} claims for policy {policy_number}")
            
        except Exception as e:
            print(f"Error fetching Guidewire claims for policy {policy_number}: {str(e)}")
            continue
    print(all_claims)
    return all_claims


def parse_policyholder_data(policyholders_data):
    parsed_policyholders = []
    
    for policyholder in policyholders_data.get('policyholders', []):
        entity = policyholder.get('entity', {})
        values = entity.get('values', {})
        
        parsed_policyholder = {
            'id': values.get('policyholder_id', [''])[0] if 'policyholder_id' in values else '',
            'firstName': values.get('first_name', [''])[0] if 'first_name' in values else '',
            'lastName': values.get('last_name', [''])[0] if 'last_name' in values else '',
            'dateOfBirth': values.get('date_of_birth', [''])[0] if 'date_of_birth' in values else '',
            'gender': values.get('gender', [''])[0] if 'gender' in values else '',
            'maritalStatus': values.get('marital_status', [''])[0] if 'marital_status' in values else '',
            'occupation': values.get('occupation', [''])[0] if 'occupation' in values else '',
            'locator': policyholder.get('locator', ''),
        }
        parsed_policyholders.append(parsed_policyholder)
    
    return parsed_policyholders

def parse_policy_data(policies_data):
    parsed_policies = []
    
    for policy in policies_data:
        try:
            # Calculate term from timestamps
            start_timestamp = float(policy.get('originalContractStartTimestamp', '0')) / 1000.0
            end_timestamp = float(policy.get('originalContractEndTimestamp', '0')) / 1000.0
            
            start_date = datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d')
            end_date = datetime.fromtimestamp(end_timestamp).strftime('%Y-%m-%d')
            term = f"{start_date} to {end_date}"

            parsed_policy = {
                'policyId': policy.get('displayId', 'N/A'),
                'product': "Personal Auto Insurance",
                'term': term,
                'status': 'Active'
            }
            parsed_policies.append(parsed_policy)
        except Exception as e:
            print(f"Error parsing policy: {str(e)}")
            # Add policy with default values if there's an error
            parsed_policy = {
                'policyId': policy.get('displayId', 'N/A'),
                'product': "Personal Auto Insurance",
                'term': 'N/A',
                'status': 'Active'
            }
            parsed_policies.append(parsed_policy)
            continue
    
    return parsed_policies

def parse_invoice_data(invoices_data):
    parsed_invoices = []
    
    for invoice in invoices_data:
        try:
            # Convert timestamps to readable dates
            created_timestamp = float(invoice.get('issuedTimestamp', '0')) / 1000.0
            due_timestamp = float(invoice.get('dueTimestamp', '0')) / 1000.0
            start_timestamp = float(invoice.get('startTimestamp', '0')) / 1000.0
            end_timestamp = float(invoice.get('endTimestamp', '0')) / 1000.0

            created_date = datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d')
            due_date = datetime.fromtimestamp(due_timestamp).strftime('%Y-%m-%d')
            billing_period = (f"{datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d')} to "
                            f"{datetime.fromtimestamp(end_timestamp).strftime('%Y-%m-%d')}")

            parsed_invoice = {
                'invoiceId': invoice.get('displayId', 'N/A'),
                'type': invoice.get('invoiceType', 'N/A'),
                'billingPeriod': billing_period,
                'dateCreated': created_date,
                'dueDate': due_date,
                'total': float(invoice.get('totalDue', '0.00')),
                'status': invoice.get('status', 'N/A')
            }
            parsed_invoices.append(parsed_invoice)
        except Exception as e:
            print(f"Error parsing invoice: {str(e)}")
            # Add invoice with default values if there's an error
            parsed_invoice = {
                'invoiceId': invoice.get('displayId', 'N/A'),
                'type': invoice.get('invoiceType', 'N/A'),
                'billingPeriod': 'N/A',
                'dateCreated': 'N/A',
                'dueDate': 'N/A',
                'total': 0.00,
                'status': 'N/A'
            }
            parsed_invoices.append(parsed_invoice)
            continue
    
    return parsed_invoices


def parse_claims_data(claims_data):
    """Parse claims data to extract required fields"""
    parsed_claims = []
    
    for claim in claims_data:
        try:
            parsed_claim = {
                'locator': claim.get('locator', 'N/A'),
                'currentStatus': claim.get('currentStatus', 'N/A'),
                'incident_type': claim.get('fieldValues', {}).get('incident_type', ['N/A'])[0],
                'incident_summary': claim.get('fieldValues', {}).get('incident_summary', ['N/A'])[0],
                'createdTimestamp': format_timestamp(claim.get('createdTimestamp', 'N/A')),
                'policyLocator': claim.get('policyLocator', 'N/A')
            }
            parsed_claims.append(parsed_claim)
        except Exception as e:
            print(f"Error parsing claim: {str(e)}")
            continue
    
    return parsed_claims

def format_timestamp(timestamp):
    """Format timestamp to readable date string"""
    try:
        if timestamp == 'N/A':
            return timestamp
        # Convert milliseconds to seconds and create datetime object
        timestamp_seconds = float(timestamp) / 1000.0
        dt = datetime.fromtimestamp(timestamp_seconds)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error formatting timestamp: {str(e)}")
        return 'N/A'

def get_policyholder_details(http, auth_token, policyholder_locator):
    """Get policies, invoices, and claims for a specific policyholder"""
    try:
        # Get policies
        policies_url = f"{SOCOTRA_ENDPOINT}/policyholder/{policyholder_locator}/policies"
        print(f"Fetching policies from: {policies_url}")
        
        policies_response = http.request(
            'GET',
            policies_url,
            headers={
                'Authorization': auth_token,
                'Content-Type': 'application/json'
            }
        )
        
        if policies_response.status != 200:
            error_message = policies_response.data.decode('utf-8')
            print(f"Failed to fetch policies: {error_message}")
            raise Exception('Failed to fetch policies')

        # Get invoices
        invoices_url = f"{SOCOTRA_ENDPOINT}/policyholder/{policyholder_locator}/invoices"
        print(f"Fetching invoices from: {invoices_url}")
        
        invoices_response = http.request(
            'GET',
            invoices_url,
            headers={
                'Authorization': auth_token,
                'Content-Type': 'application/json'
            }
        )
        
        if invoices_response.status != 200:
            error_message = invoices_response.data.decode('utf-8')
            print(f"Failed to fetch invoices: {error_message}")
            raise Exception('Failed to fetch invoices')

        policies_data = json.loads(policies_response.data.decode('utf-8'))
        invoices_data = json.loads(invoices_response.data.decode('utf-8'))
        
        parsed_policies = parse_policy_data(policies_data)
        parsed_invoices = parse_invoice_data(invoices_data)

        # Get claims for each policy
        all_claims = []
        for policy in parsed_policies:
            claims_url = f"{SOCOTRA_ENDPOINT}/policy/{policy['policyId']}/claims"
            print(f"Fetching claims from: {claims_url}")
            
            claims_response = http.request(
                'GET',
                claims_url,
                headers={
                    'Authorization': auth_token,
                    'Content-Type': 'application/json'
                }
            )
            
            if claims_response.status == 200:
                claims_data = json.loads(claims_response.data.decode('utf-8'))
                parsed_claims = parse_claims_data(claims_data)
                all_claims.extend(parsed_claims)
            else:
                print(f"Failed to fetch claims for policy {policy['policyId']}: {claims_response.data.decode('utf-8')}")

        return {
            'policies': parsed_policies,
            'invoices': parsed_invoices,
            'claims': all_claims
        }
    except Exception as e:
        print(f"Error in get_policyholder_details: {str(e)}")
        raise e


def lambda_handler(event, context):
    http = urllib3.PoolManager()
    print(event)

    try:
        # Parse input parameters
        if isinstance(event, str):
            body = json.loads(event)
        else:
            body = event  # If event is already a dict
            
        datasource = body.get('dataSource')  # Note: Changed from 'datasource' to 'dataSource'
        policyholder_locator = body.get('policyholderLocator')
        policy_numbers=["PY1234","PY0001","PY4321","PY4000"]

        print(f"Received parameters - dataSource: {datasource}, "
              f"policyholderLocator: {policyholder_locator}, "
              f"policyNumbers: {policy_numbers}")


    except Exception as e:
        print(f"Error parsing input: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Invalid input format',
                'message': str(e)
            })
        }

    try:
        if datasource and datasource.lower() == 'guidewire':
            auth_headers = urllib3.make_headers(
                    basic_auth=f'{GW_USERNAME}:{GW_PASSWORD}'
                )
            http = urllib3.PoolManager(headers=auth_headers)
                
            claims = get_guidewire_claims(http, policy_numbers)
                
            return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'claims': claims
                    })
                }
        else:
            # Validate environment variables
            if not all([SOCOTRA_HOST, SOCOTRA_USERNAME, SOCOTRA_PASSWORD]):
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Missing required environment variables'
                    })
                }

            # Authentication request
            auth_url = f"{SOCOTRA_ENDPOINT}/account/authenticate"
            auth_body = {
                "hostName": SOCOTRA_HOST,
                "username": SOCOTRA_USERNAME,
                "password": SOCOTRA_PASSWORD
            }
            
            print(f"Making auth request to: {auth_url}")
            
            auth_response = http.request(
                'POST',
                auth_url,
                headers={
                    'Content-Type': 'application/json'
                },
                body=json.dumps(auth_body)
            )
            
            if auth_response.status != 200:
                error_message = auth_response.data.decode('utf-8')
                print(f"Authentication failed: {error_message}")
                return {
                    'statusCode': auth_response.status,
                    'body': json.dumps({
                        'error': 'Authentication failed',
                        'message': error_message
                    })
                }
            
            # Parse authentication response
            auth_data = json.loads(auth_response.data.decode('utf-8'))
            auth_token = auth_data.get('authorizationToken')
            
            if not auth_token:
                print("No authorization token received")
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'No authorization token received'
                    })
                }

            # Handle API calls based on input parameters
            if policyholder_locator:
                # If policyholder_locator is provided, just print the message
                message = f"Fetching policyholder details for locator: {policyholder_locator}"
                print(message)
                customer_details = get_policyholder_details(http, auth_token, policyholder_locator)
                print(customer_details)
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'message': customer_details
                    })
                }
            else:
                # If no policyholder_locator, fetch all policyholders
                policyholders_url = f"{SOCOTRA_ENDPOINT}/policyholders"
                print(f"Fetching policyholders from: {policyholders_url}")
                
                policyholders_response = http.request(
                    'GET',
                    policyholders_url,
                    headers={
                        'Authorization': auth_token,
                        'Content-Type': 'application/json'
                    }
                )
                
                if policyholders_response.status != 200:
                    error_message = policyholders_response.data.decode('utf-8')
                    print(f"Failed to fetch policyholders: {error_message}")
                    return {
                        'statusCode': policyholders_response.status,
                        'body': json.dumps({
                            'error': 'Failed to fetch policyholders',
                            'message': error_message
                        })
                    }
                
                policyholders_data = json.loads(policyholders_response.data.decode('utf-8'))
                parsed_policyholders = parse_policyholder_data(policyholders_data)
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({'policyholders': parsed_policyholders})
                }
                    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
                'body': json.dumps({
                    'error': 'Internal server error',
                    'message': str(e)
                })
        }
