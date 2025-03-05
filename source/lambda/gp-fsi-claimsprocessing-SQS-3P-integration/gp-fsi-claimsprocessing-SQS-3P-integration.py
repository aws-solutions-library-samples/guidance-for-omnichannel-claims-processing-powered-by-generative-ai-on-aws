import json
import os
import urllib3
from datetime import datetime
import base64
import re

# Environment variables
SOCOTRA_HOST = os.environ['SOCOTRA_HOST']
SOCOTRA_USERNAME = os.environ['SOCOTRA_USERNAME']
SOCOTRA_PASSWORD = os.environ['SOCOTRA_PASSWORD']
SOCOTRA_ENDPOINT = os.environ.get('SOCOTRA_ENDPOINT')

# Get credentials from environment variables
GW_USERNAME = os.getenv('GW_USERNAME')  # Fallback to 'su' if not set
GW_PASSWORD = os.getenv('GW_PASSWORD')  # Fallback to 'gw' if not set
# Base URL with the correct path structure
GW_BASE_URL = os.getenv('GW_BASE_URL')

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat() + 'Z'
        return super().default(obj)


def extract_claim_number(response_data):
    """
    Extracts the claim number from the response data.
    """
    try:
        # Iterate through all responses
        for response in response_data.get('responses', []):
            body = response.get('body', {})
            data = body.get('data', {})
            attributes = data.get('attributes', {})
            
            # Get assignment status and claim number if they exist
            assignment_status = attributes.get('assignmentStatus', {})
            claim_number = attributes.get('claimNumber')
            
            # Check if status is assigned and claim number exists
            if (assignment_status.get('code') == 'assigned' and 
                assignment_status.get('name') == 'Assigned' and 
                claim_number):
                #print(claim_number)
                return claim_number
                
    except Exception as e:
        print(f"Error processing response: {str(e)}")
    
    return None


def create_unverified_policy_and_claim(base_url, username, password, policy_number, loss_date, first_name, last_name, policy_type="PersonalAuto"):
    """
    Creates an unverified policy and associated claim using the composite API with Basic Auth.
    """
    #loss_date = json.dumps(loss_date)
    loss_date = loss_date.strftime("%Y-%m-%dT%H:%M:%S.00Z")
    # Disable SSL verification warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Create a connection pool manager with SSL verification disabled
    http = urllib3.PoolManager(
        cert_reqs='CERT_NONE',
        assert_hostname=False
    )
    
    # Set up the headers with Basic Auth
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }
    
    # Construct the composite request payload
    payload = {
        "requests": [
            {
                "method": "post",
                "uri": "/claim/v1/unverified-policies",
                "body": {
                    "data": {
                        "attributes": {
                            "policyNumber": policy_number,
                            "policyType": {
                                "code": policy_type
                            }
                        }
                    }
                }
            },
            {
                "method": "post",
                "uri": "/claim/v1/claims",
                "body": {
                    "data": {
                        "attributes": {
                            "lossDate": loss_date,
                            "policyNumber": policy_number
                        }
                    }
                },
                "vars": [
                    {
                        "name": "claimId",
                        "path": "$.data.attributes.id"
                    }
                ]
            },
            {
                "method": "post",
                "uri": "/claim/v1/claims/${claimId}/contacts",
                "body": {
                    "data": {
                        "attributes": {
                            "contactSubtype": "Person",
                            "firstName": first_name,
                            "lastName": last_name
                        }
                    }
                },
                "vars": [
                    {
                        "name": "contactId",
                        "path": "$.data.attributes.id"
                    }
                ]
            },
            {
                "method": "patch",
                "uri": "/claim/v1/claims/${claimId}",
                "body": {
                    "data": {
                        "attributes": {
                            "reporter": {
                                "id": "${contactId}"
                            }
                        }
                    }
                }
            },
            {
                "method": "post",
                "uri": "/claim/v1/claims/${claimId}/submit"
            }
        ]
    }
    
    try:
        # Make the composite API request
        endpoint = "/composite/v1/composite"  # Updated endpoint path
        url = f"{base_url.rstrip('/')}{endpoint}"
        
        print(f"Making request to: {url}")  # Debug print
        
        encoded_data = json.dumps(payload).encode('utf-8')
        
        response = http.request(
            'POST',
            url,
            body=encoded_data,
            headers=headers
        )
        
        # Check if the request was successful
        if response.status != 200:
            print(f"Error: HTTP {response.status}")
            print(f"Response content: {response.data}")
            return None
            
        # Return the response data
        return json.loads(response.data.decode('utf-8'))
        
    except urllib3.exceptions.RequestError as e:
        print(f"Error making API request: {str(e)}")
        return None
    finally:
        # Clean up
        http.clear()

def guidewire_integration(PolicyNumber,CustomerName,loss_date):

    
    if not GW_USERNAME or not GW_PASSWORD:
        print("Error: API_USERNAME and API_PASSWORD environment variables must be set for Guidewire")
        return

    print("Calling create_unverified_policy_and_claim")
    # Make the API call
    result = create_unverified_policy_and_claim(
        base_url=GW_BASE_URL,
        username=GW_USERNAME,
        password=GW_PASSWORD,
        policy_number=PolicyNumber,
        loss_date=loss_date,
        first_name=CustomerName.split(" ")[0],
        last_name=CustomerName.split(" ")[1]
    )
    
    # Print the result
    if result:
        print("Successfully created unverified policy and claim:")
        print(json.dumps(result))
        
        # Extract and print the claim number
        claim_number = extract_claim_number(result)
        if claim_number:
            print(f"\nGuidewire Claim Number: {claim_number}")
            return claim_number
        else:
            print("\nClaim Number not found in response")
    else:
        print("Failed to create unverified policy and claim")


def format_datetime(date_str):
    """
    Format date string to standard format, adding default time if needed
    
    Args:
        date_str (str): Date string in various possible formats
    
    Returns:
        datetime: Formatted datetime object
    """
    if not date_str:
        return datetime.utcnow()
        
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%S.%fZ",      # 2023-01-01T12:00:00.000Z
        "%Y-%m-%d %H:%M:%S",          # 2023-01-01 13:20:20
        "%Y-%m-%d",                    # 2023-01-01
        "%m/%d/%Y %H:%M:%S",          # 01/01/2023 13:20:20
        "%m/%d/%Y",                    # 01/01/2023
        "%d-%m-%Y %H:%M:%S",          # 01-01-2023 13:20:20
        "%d-%m-%Y",                    # 01-01-2023
        "%Y/%m/%d %H:%M:%S",          # 2023/01/01 13:20:20
        "%Y/%m/%d"                     # 2023/01/01
    ]
    
    # Clean up the input string
    date_str = date_str.strip()
    
    for date_format in formats_to_try:
        try:
            date_obj = datetime.strptime(date_str, date_format)
            # If no time component in the format, add default time
            if date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                date_obj = date_obj.replace(hour=1, minute=1, second=1, microsecond=0)
            return date_obj
        except ValueError:
            continue
    
    # If no format matched, try to parse date and time separately
    try:
        # Split into date and time parts
        if ' ' in date_str:
            date_part, time_part = date_str.split(' ', 1)
        else:
            date_part = date_str
            time_part = "01:01:01"
            
        # Try to parse date part
        for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
            try:
                date_obj = datetime.strptime(date_part, date_format)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse date part: {date_part}")
            
        # Try to parse time part
        try:
            time_obj = datetime.strptime(time_part, "%H:%M:%S")
            # Combine date and time
            date_obj = date_obj.replace(
                hour=time_obj.hour,
                minute=time_obj.minute,
                second=time_obj.second,
                microsecond=0
            )
            return date_obj
        except ValueError:
            # If time parsing fails, use default time
            return date_obj.replace(hour=1, minute=1, second=1, microsecond=0)
            
    except Exception as e:
        print(f"Error parsing date string '{date_str}': {str(e)}")
        raise ValueError(f"Unable to parse date string: {date_str}")



def authenticate_socotra(http):
    auth_url = f"{SOCOTRA_ENDPOINT}/account/authenticate"
    auth_body = {
        "hostName": SOCOTRA_HOST,
        "username": SOCOTRA_USERNAME,
        "password": SOCOTRA_PASSWORD
    }
    
    auth_response = http.request(
        'POST',
        auth_url,
        headers={'Content-Type': 'application/json'},
        body=json.dumps(auth_body)
    )
    
    if auth_response.status != 200:
        raise Exception(f"Authentication failed: {auth_response.data.decode('utf-8')}")
    
    auth_data = json.loads(auth_response.data.decode('utf-8'))
    return auth_data.get('authorizationToken')

def get_policy_locator(http, auth_token, external_id):
    """Fetch policies for the policyholder using external_id and return the most recent policy regardless of status"""
    policies_url = f"{SOCOTRA_ENDPOINT}/policyholder/{external_id}/policies"
    
    print(f"Fetching policies for policyholder: {external_id}")
    
    policies_response = http.request(
        'GET',
        policies_url,
        headers={
            'Content-Type': 'application/json',
            'Authorization': auth_token
        }
    )
    
    if policies_response.status != 200:
        raise Exception(f"Failed to get policies: {policies_response.data.decode('utf-8')}")
    
    # Log raw response
    raw_response = policies_response.data.decode('utf-8')
    print(f"Raw API response: {raw_response}")
    
    policies_data = json.loads(raw_response)
    #print(f"Response type: {type(policies_data)}")
    #print(f"Response content: {json.dumps(policies_data, indent=2)}")
    
    try:
        policies_list = []
        
        # Handle response as either list or dictionary
        all_policies = policies_data if isinstance(policies_data, list) else policies_data.get('policies', [])
        
        # Collect all policies with their timestamps
        for policy in all_policies:
            locator = policy.get('locator')
            status = policy.get('status', 'N/A')
            # Try both timestamp fields
            timestamp = policy.get('startTimestamp') or policy.get('createdTimestamp')
            
            print(f"Checking policy - Status: {status}, Locator: {locator}, Timestamp: {timestamp}")
            
            if locator and timestamp:
                policies_list.append({
                    'locator': locator,
                    'timestamp': int(timestamp),  # Convert to int for comparison
                    'status': status
                })
        
        if not policies_list:
            print("No policies found")
            return None
            
        # Sort policies by timestamp in descending order (most recent first)
        sorted_policies = sorted(policies_list, key=lambda x: x['timestamp'], reverse=True)
        
        # Log all policies for debugging
        print(f"Found {len(sorted_policies)} policies:")
        for idx, policy in enumerate(sorted_policies):
            print(f"{idx + 1}. Locator: {policy['locator']}, Status: {policy['status']}, Timestamp: {policy['timestamp']}")
        
        # Return the most recent policy locator
        most_recent_policy = sorted_policies[0]
        print(f"Selected most recent policy - Locator: {most_recent_policy['locator']}, Status: {most_recent_policy['status']}")
        return most_recent_policy['locator']
        
    except Exception as e:
        print(f"Error processing policies response in Socotra: {str(e)}")
        print(f"Response data type: {type(policies_data)}")
        print(f"Response data: {policies_data}")
        raise


def create_claim(http, auth_token, policy_locator):
    claims_url = f"{SOCOTRA_ENDPOINT}/claim"
    
    # Initial claim creation body
    claim_body = {
        "policyLocator": policy_locator
    }
    
    print(f"Creating claim for policy: {policy_locator}")
    
    claim_response = http.request(
        'POST',
        claims_url,
        headers={
            'Content-Type': 'application/json',
            'Authorization': auth_token
        },
        body=json.dumps(claim_body)
    )
    
    if claim_response.status != 200:
        raise Exception(f"Failed to create claim: {claim_response.data.decode('utf-8')}")
    
    response_data = json.loads(claim_response.data.decode('utf-8'))
    print(f"Claim created successfully in Socotra")
    return response_data

def update_claim_details(http, auth_token, claim_locator, sqs_message,loss_date_ms,created_at_ms):
    try:
        update_url = f"{SOCOTRA_ENDPOINT}/claim/{claim_locator}/update"
        
        # Convert timestamps to datetime objects with proper error handling
  
        
        # Prepare the update body
        update_body = {
            "fieldValues": {
                "incident_type": ["Collision"],
                "fraud_check": ["Genuine"],
                "incident_summary": [sqs_message.get('Details', '')],
            },
            "incidentTimestamp": loss_date_ms,
            "notificationTimestamp": created_at_ms,
            "status": "open"
        }
        
        print(f"Updating claim {claim_locator} with details: {json.dumps(update_body, indent=2)}")
        
        update_response = http.request(
            'POST',
            update_url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': auth_token
            },
            body=json.dumps(update_body)
        )
        
        if update_response.status != 200:
            raise Exception(f"Failed to update claim: {update_response.data.decode('utf-8')}")
        
        response_data = json.loads(update_response.data.decode('utf-8'))
        print("Claim updated successfully in Socotra")
        return response_data
        
    except Exception as e:
        logger.error(f"Error updating claim details in Socotra: {str(e)}")
        raise

    
def test_connection():
    try:
        http = urllib3.PoolManager(
        timeout=urllib3.Timeout(
                    connect=5.0,
                    read=10.0
                )
        )
        response = http.request(
                "GET", 
                f"{SOCOTRA_ENDPOINT}/account/authenticate",
                timeout=30.0
        )
        print(response)
        return {
                'status': response.status,
                'data': response.data.decode('utf-8')
            }
    except Exception as e:
        return str(e)



def socotra_integration(external_id,sqs_message,loss_date_ms,created_at_ms):
    http = urllib3.PoolManager()
    #test_connection()
    try:
        print("Attempting to process message to Socotra")
        # Authenticate with Socotra
        auth_token = authenticate_socotra(http)
            
        # Get policy locator using external_id
        policy_locator = get_policy_locator(http, auth_token, external_id)
        print(f"Found policy locator: {policy_locator}")
            
        if not policy_locator:
            raise ValueError(f"No active policy found for external_id: {external_id}")
            
        # Create initial claim
        claim_response = create_claim(http, auth_token, policy_locator)
        claim_locator = claim_response.get('locator')
        print(f"claim_locator: {claim_locator}")
            
        if not claim_locator:
            raise ValueError("Failed to get claim locator from response")
                
        # Update claim details
        updated_claim = update_claim_details(http, auth_token, claim_locator, sqs_message,loss_date_ms,created_at_ms)
        return policy_locator,claim_locator,updated_claim    
    
    except Exception as e:
        print(f"Error processing message to Socotra: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process message to Socotra',
                'message': str(e)
            })
        }

    
    
def lambda_handler(event, context):
    print("Received event:", event)
    try:
        # Parse SQS message
        if 'Records' in event and len(event['Records']) > 0:
            message_body = event['Records'][0]['body']
            if isinstance(message_body, str):
                sqs_message = json.loads(message_body)
            else:
                sqs_message = message_body
        else:
            raise ValueError("No valid SQS message found in event")

        external_id = sqs_message.get('External_Id')
        print(f"Extracted External_Id: {external_id}")

        PolicyNumber = sqs_message.get('PolicyNumber')
        print(f"Extracted PolicyNumber: {PolicyNumber}")

        if not external_id:
            raise ValueError("External_Id not found in SQS message")
        
        if not PolicyNumber:
            raise ValueError("PolicyNumber not found in SQS message")
        
        try:
            # Parse and format dates
            loss_date = format_datetime(sqs_message.get('LossDate'))
            created_at = format_datetime(sqs_message.get('CreatedAt', 
                                      datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")))
            
            # Convert to milliseconds
            loss_date_ms = int(loss_date.timestamp() * 1000)
            created_at_ms = int(created_at.timestamp() * 1000)
            
            print(f"Processed dates - Loss Date: {loss_date}, Created At: {created_at}")
            
        except ValueError as e:
            print(f"Date parsing error: {str(e)}")
            # Use current time as fallback
            now = datetime.utcnow()
            loss_date_ms = int(now.timestamp() * 1000)
            created_at_ms = loss_date_ms

        CustomerName = sqs_message.get('CustomerName')
        print(f"CustomerName: {CustomerName}")

        # Call integration functions
        print("Socotra Integration starting")
        policy_locator, claim_locator, updated_claim = socotra_integration(
            external_id, 
            sqs_message, 
            loss_date_ms, 
            created_at_ms
        )
        print("Socotra Integration Completed")
        print("Guidewire Integration starting")
        claim_number = guidewire_integration(
            PolicyNumber,
            CustomerName,
            loss_date
        )
        print("Guidewire Integration Completed")
        # Prepare response data
        response_data = {
            'message': 'Claim created and updated successfully in Socotra and Guidewire',
            'socotra_externalId': external_id,
            'socotra_policyLocator': policy_locator,
            'socotra_claimLocator': claim_locator,
            'socotra_updatedClaim': updated_claim,
            'gw_policy_number': PolicyNumber,
            'gw_claim_number': claim_number
        }

        return {
            'statusCode': 200,
            'body': json.dumps(response_data, cls=DateTimeEncoder)
        }

    except Exception as e:
        error_message = str(e)
        print(f"Error processing message: {error_message}")
        
        error_response = {
            'error': 'Failed to process message',
            'message': error_message,
            'timestamp': datetime.utcnow()  # Include error timestamp
        }
        
        return {
            'statusCode': 500,
            'body': json.dumps(error_response, cls=DateTimeEncoder)
        }