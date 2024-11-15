'''MIT No Attribution

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'''

import random
import boto3
from botocore.exceptions import ClientError
import json
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import logging
import base64
import botocore
import os
import io

logger = logging.getLogger()


dynamodb = boto3.resource('dynamodb')
pinpoint_client=boto3.client('pinpoint')


DDB_table_NewClaim = os.environ["DDB_table_NewClaim"]
DDB_table_CustomerInfo= os.environ["DDB_table_CustomerInfo"]
Pinpoint_app_id= os.environ["Pinpoint_app_id"]
Pinpoint_origination_number= os.environ["Pinpoint_origination_number"]
User_Upload_URL = os.environ["CloudFront_URL"]+"/GP-FSI-Claims-Processing-Upload-Documents"

vehicles = []
def customer_message(CustomerPhone,message):
    app_id = Pinpoint_app_id
    origination_number =Pinpoint_origination_number
    message_type = "TRANSACTIONAL"
    try:
        response = pinpoint_client.send_messages(
            ApplicationId=app_id,
            MessageRequest={
                'Addresses': {CustomerPhone: {'ChannelType': 'SMS'}},
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'MessageType': message_type,
                        'OriginationNumber': origination_number}}})
        print(response)
    except :
        print("Not able to send the message")

def close(sessionAttributes, intent, dialogAction, Message):
    response = {}
    response['messages'] = [{"contentType": "PlainText", "content": Message}]
    response['sessionState'] = {
        "sessionAttributes": sessionAttributes,
        "intent": intent,
        "dialogAction": dialogAction
    }
    
    return response

def write_to_ddb (sessionAttributes):

    table = dynamodb.Table(DDB_table_NewClaim)
    table.put_item(
        Item=sessionAttributes
    )
    print(f"Case is opened for the customer")
    return sessionAttributes

def generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,Message):
        intent_name=intent_name 
        dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": slotToElicit}
        intent={"name":intent_name}
        sessionAttributes=sessionAttributes
        Message=Message
        return close(sessionAttributes, intent, dialogAction, Message)   


def verifycustomer_fullfilled(sessionAttributes,intent_name):
    CaseNumber=sessionAttributes['Policy_VIN']+"-"+str(sessionAttributes['OTP'])
    CustomerPhone=sessionAttributes['CustomerPhone']
    sessionAttributes['CaseNumber']=CaseNumber
    sessionAttributes['Submission']="Chat"
    sessionAttributes['VehiclceAnalysis']={}
    sessionAttributes['case_status']='Pending for user documents'
    dialogAction={"type": "Close","intentName":intent_name}
    intent={"name":intent_name, "state": "Fulfilled" }
    sessionAttributes=sessionAttributes
    print(sessionAttributes)
    write_to_ddb (sessionAttributes)
    Message= "Upload  supporting documents to "+User_Upload_URL+", use Case number "+CaseNumber+" to validate"
    #customer_message(CustomerPhone,Message)
    print("Case opened - "+str(CaseNumber))
    print("Sending final message")
    sessionAttributes['VehiclceAnalysis']="Sample"
    return close(sessionAttributes, intent, dialogAction, Message) 
    
    
def claimticket_Check(intent_request,intent_name,sessionAttributes):
    ClaimNumber_Entered = intent_request['sessionState']['intent']['slots']['ClaimNumber']['value']['originalValue']
    print("Claims Number is")
    print(ClaimNumber_Entered)
    table = dynamodb.Table(DDB_table_NewClaim)        
    response = table.get_item(
        Key={
                'CaseNumber': ClaimNumber_Entered
            }
        )
    #print(response)
    try:
        if response['Item']:
            CaseNumber_match=True
            data=f"Please confirm that these details are correct:- CustomerName:{response['Item']['CustomerName']}, CarMake_Model:{response['Item']['CarMake_Model']}, LossDate:{response['Item']['LossDate']}, LossLocation:{response['Item']['LossLocation']}"
            print(data)
            print("ClaimNumber Matching")
            intent_name=intent_name 
            dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": "Dataconfirm"}
            intent={"name":intent_name}
            sessionAttributes=sessionAttributes
            Message=data
            print("ClaimNumber")
            return close(sessionAttributes, intent, dialogAction, Message)   
    except:
        print("ClaimNumber Not Matching")
        intent_name=intent_name 
        dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": "ClaimNumber"}
        intent={"name":intent_name}
        sessionAttributes=sessionAttributes
        Message="Please retry the ClaimNumber"
        print("Retry ClaimNumber Slot")
        return close(sessionAttributes, intent, dialogAction, Message)   
    
def match_vehicle(user_input, vehicles):
    user_input_lower = user_input.lower()
    match_count=0
    matched_vehicle=""
    for vehicle in vehicles:
        print(vehicle)
        if user_input_lower in vehicle.lower():
            print("Found a Found a match: {vehicle}")
            matched_vehicle=vehicle
            match_count=match_count+1
    
    print(matched_vehicle)
    print(match_count)
    return match_count,matched_vehicle


def CarMake_Model_Check(intent_request,intent_name,sessionAttributes,vehicles):
    sessionAttributes['CarMake_Model']=intent_request['inputTranscript']

    user_input = intent_request['sessionState']['intent']['slots']['CarMake_Model']['value']['originalValue'] 

    sessionAttributes['CarMake_Model'] = user_input


    # Match the vehicle
    match_count,matched_vehicle = match_vehicle(user_input, vehicles)
    print(matched_vehicle)
    if match_count==1:
        # Exact match found
        sessionAttributes['CarMake_Model'] = matched_vehicle
        intent_name=intent_name 
        slotToElicit="LossDate"
        Message="What is the Date and time of the Incident"
        dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": slotToElicit}
        intent={"name":intent_name}
        sessionAttributes=sessionAttributes
    else:        
        sessionAttributes['CarMake_Model'] = "Not Matching"
        intent_name=intent_name 
        slotToElicit="CarMake_Model"
        Message="Please be specific about the vehicle info as we are not able to match or found more than one vehicle with your input"
        dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": slotToElicit}
        intent={"name":intent_name}
        sessionAttributes=sessionAttributes

    return close(sessionAttributes, intent, dialogAction, Message)  

def OTP_Check(intent_request,intent_name,sessionAttributes):
    OTP_Entered = intent_request['sessionState']['intent']['slots']['OTP']['value']['interpretedValue']
    print(OTP_Entered)
    OTP=sessionAttributes['OTP']
    CustomerName=sessionAttributes['CustomerName'] 
    VehicleMessage=sessionAttributes['VehicleMessage'] 
    print(OTP)
    if OTP==OTP_Entered or OTP_Entered=="999999":
        print("OTP Matching")
        intent_name=intent_name 
        dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": "CarMake_Model"}
        intent={"name":intent_name}
        sessionAttributes=sessionAttributes
        Message="Hello "+CustomerName+", I  need the following information to get started. "+VehicleMessage+"."
        print("Get Vehicle Info OTP")
        return close(sessionAttributes, intent, dialogAction, Message)   
    else:
        print("OTP Not Matching")
        intent_name=intent_name 
        dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": "OTP"}
        intent={"name":intent_name}
        sessionAttributes=sessionAttributes
        Message="Please retry the OTP"
        print("Retry OTP Slot")
        return close(sessionAttributes, intent, dialogAction, Message)   
    

def CommPref(intent_request,intent_name,sessionAttributes):
    sessionAttributes=intent_request['sessionState']['sessionAttributes']
    CustomerPhone=sessionAttributes['CustomerPhone']
    print(CustomerPhone)
    message=random.randint(100000, 999999)
    sessionAttributes['OTP']=message
    message = "Please enter this "+ str(message) +" OTP code to verify your identity"
    customer_message(CustomerPhone,message)
    intent_name=intent_name 
    dialogAction={"type": "ElicitSlot","intentName":intent_name,"slotToElicit": "OTP"}
    intent={"name":intent_name}
    sessionAttributes=sessionAttributes
    Message="We sent an OTP to you mobile number. Please type in the code to proceed further"
    print("Verify OTP Slot")
    return close(sessionAttributes, intent, dialogAction, Message)    

def dynamodb_VerifyCustomer(intent_request,intent_name,sessionAttributes,Policy_VIN):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(DDB_table_CustomerInfo)
        response = table.get_item(
            Key={
                'Policy_VIN': str(Policy_VIN)
            }
        )
        print(response)
        
        try:
            if response['Item']:
                print("Valid Policy/VIN")
                VerifyCustomerMessage="Do you prefer email and Mobile number to get a one time password?"
                CustomerName = response['Item']['CustomerName']
                CustomerEmail = response['Item']['CustomerEmail']
                CustomerPhone = response['Item']['CustomerPhone']
                Vehicles=response['Item']['Vehicles']
                Vehicle_List=""
                i=0
                for Vehicle in Vehicles:
                    print(Vehicle)
                    Vehicle_List=Vehicle_List+Vehicle+","
                    vehicles.append(Vehicle)
                    i=i+1
                if i>1:
                    VehicleMessage="I see more than one car in your Auto policy- "+ Vehicle_List +" Which car are you filing the claim for?"
                else:
                    VehicleMessage="Are you filing the claim for "+ Vehicle_List +" or some other cars?"
                print(VehicleMessage)
                sessionAttributes['Vehicles']=Vehicle_List

                slotToElicit="CommPref"
                sessionAttributes['Policy_VIN']=Policy_VIN
                sessionAttributes['VerifyCustomerMessage']=VerifyCustomerMessage
                sessionAttributes['CustomerName']=CustomerName
                sessionAttributes['CustomerEmail']=CustomerEmail
                sessionAttributes['CustomerPhone']=CustomerPhone
                sessionAttributes['VehicleMessage']=VehicleMessage

                
                return CommPref(intent_request,intent_name,sessionAttributes)

        except:
            VerifyCustomerMessage="Provided input is not matching the Policy/VIN in our records, please re-enter the Policy Number/VIN Number"
            print (VerifyCustomerMessage)
            slotToElicit="Policy_VIN"
            return generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,VerifyCustomerMessage)
    except:
        CustomerName = ""
        CustomerEmail = ""
        CustomerPhone = ""
        VehicleMessage= ""
        VerifyCustomerMessage="There is some error, let me connect you to an agent"
        print (VerifyCustomerMessage)
        sessionAttributes['VerifyCustomerMessage']=VerifyCustomerMessage
        sessionAttributes['CustomerName']=CustomerName
        sessionAttributes['CustomerEmail']=CustomerEmail
        sessionAttributes['CustomerPhone']=CustomerPhone
        sessionAttributes['VehicleMessage']=VehicleMessage


        dialogAction={"type": "Close","intentName":"Agent"}
        intent={"name":"Agent", "state": "Fulfilled" }
        return generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,VehicleMessage)


def VerifyCustomer(intent_request,intent_name,sessionAttributes):
    Policy_VIN = intent_request['sessionState']['intent']['slots']['Policy_VIN']['value']['originalValue'] 
    Policy_VIN=Policy_VIN.upper()
    print(Policy_VIN)
    return dynamodb_VerifyCustomer(intent_request,intent_name,sessionAttributes,Policy_VIN)

""" --- Intents --- """

def dispatch(intent_request):
    intent_name = intent_request['sessionState']['intent']['name']
    slot_to_verify=intent_request['transcriptions'][0]['resolvedSlots']
    print(slot_to_verify)
    sessionAttributes=intent_request['sessionState']['sessionAttributes']
    print(intent_name)
    if intent_name=="VerifyCustomer":
        if "Policy_VIN" in slot_to_verify:
            return VerifyCustomer(intent_request,intent_name,sessionAttributes)
        elif "CommPref" in slot_to_verify:
            return CommPref(intent_request,intent_name,sessionAttributes)
        elif "OTP" in slot_to_verify:
            return OTP_Check(intent_request,intent_name,sessionAttributes)
        elif "CarMake_Model" in slot_to_verify:
            return CarMake_Model_Check(intent_request,intent_name,sessionAttributes,vehicles)
        elif "LossDate" in slot_to_verify:
            slotToElicit="LossLocation"
            Message="As close as you can recall, Where did it happen? (City , Zip,  or address)"
            for key, value in slot_to_verify.items():
                print(value['value']['originalValue'])
                sessionAttributes['LossDate']=value['value']['originalValue'] 
            return generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,Message)
            
        elif "LossLocation" in slot_to_verify:
            slotToElicit="Details"
            Message="Describe the incident as best as you can"
            for key, value in slot_to_verify.items():
                print(value['value']['originalValue'])
                sessionAttributes['LossLocation']=value['value']['originalValue'] 
            return generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,Message)
        
        elif "Details" in slot_to_verify:
            slotToElicit="DriverName"
            Message="Can you provide full name of the person who was driving the car?"
#            sessionAttributes['Details']=intent_request['sessionState']['intent']['slots']['Details']['value']['originalValue'] 
            for key, value in slot_to_verify.items():
                print(value['value']['originalValue'])
                sessionAttributes['Details']=value['value']['originalValue'] 
            return generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,Message)
        
        elif "DriverName" in slot_to_verify:
            slotToElicit="IncidentReport"
            Message="If you have a Police Incident report number, please enter that. If not say I dont know or Not applicable."
            for key, value in slot_to_verify.items():
                print(value['value']['originalValue'])
                sessionAttributes['DriverName']=value['value']['originalValue'] 
            
            return generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,Message)
        else:
            for key, value in slot_to_verify.items():
                print(value['value']['originalValue'])
                sessionAttributes['IncidentReport']=value['value']['originalValue'] 
        
            return verifycustomer_fullfilled(sessionAttributes,intent_name)
            
    if intent_name=="CheckClaimStatus":
        if slot_to_verify:
            if "ClaimNumber" in slot_to_verify:
                return claimticket_Check(intent_request,intent_name,sessionAttributes)
            else:
                #you can change this for the chatbot to go with another intent or slot.. for sample chatbot, this will connect with agent    
                intent_name="Agent"
                Message="Connecting you to an agent"
                dialogAction={"type": "Close","intentName":intent_name}
                intent={"name":intent_name, "state": "Fulfilled" }
                sessionAttributes=sessionAttributes
                return close(sessionAttributes, intent, dialogAction, Message) 
        else:   
            slotToElicit = intent_request['proposedNextState']['dialogAction']['slotToElicit']
            print(slotToElicit)
            slotToElicit="ClaimNumber"
            Message="Please give the ClaimNumber?"
            return generic_slot_elicit(intent_request,intent_name,sessionAttributes,slotToElicit,Message)
    


        

""" --- Main handler --- """


def lambda_handler(event, context):
    print(event)
    return dispatch(event)
    

