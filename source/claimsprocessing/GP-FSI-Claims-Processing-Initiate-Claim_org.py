
import boto3
import streamlit as st
import time
from boto3.dynamodb.conditions import Key
import random


st.set_page_config(page_title="Submit a new claim")

st.title('Initiate a new claim')

region_name="replace_region_name"
app_id="replace_Pinpoint_app_id"
origination_number="replace_Pinpoint_origination_number"
DDBtableNewClaim="replace_DDBtableNewClaim"
DDBtableCustomerInfo="replace_DDBtableCustomerInfo"


pinpoint_client=boto3.client('pinpoint')
dynamodb = boto3.resource('dynamodb',region_name=region_name)


def customer_message(CustomerPhone,Policy_VIN):
    OTP = random.randint(100000, 999999)
    OTP=str(OTP)
    message = "Please enter this "+ str(OTP) +" OTP code to verify your identity"
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
        try:
            CaseNumber=Policy_VIN+"-"+str(OTP)

            table = dynamodb.Table(DDBtableNewClaim)
            table.put_item(
                Item={  
                    'CaseNumber': CaseNumber,
                    'Policy_VIN':PolicyVinNumber,
                    'Submission':'Form'
                }
            )
        except :
            st.write("Not able to write to the DDB")
        
    except :
        st.write("Not able to send the message")

    
    
PolicyVinNumber=st.text_input("Enter your policy or VIN number","PY1234")

if PolicyVinNumber:
    table = dynamodb.Table(DDBtableCustomerInfo)        
    response = table.get_item(
        Key={
                'Policy_VIN': PolicyVinNumber
            }
        )
    #st.write(response)
    try:
        if response['Item']:
            #st.write(response)
            CustomerPhone=response['Item']['CustomerPhone']
            CustomerName=response['Item']['CustomerName']
            CustomerEmail=response['Item']['CustomerEmail']
            Vehicles=response['Item']['Vehicles']

            
            if st.button("Generate OTP"):
                customer_message(CustomerPhone,PolicyVinNumber)
            
            otptoken=st.text_input("Enter the OTP here")
            if otptoken:
                table = dynamodb.Table(DDBtableNewClaim)        
                response = table.get_item(
                Key={
                    'CaseNumber': PolicyVinNumber+"-"+str(otptoken)
                }
                )
                #st.write(response)
                try:
                    if response['Item']:
                        st.write("OTP Verified")

                        CarMake_Model = st.selectbox(
                                "Which car are you filing the claim for?",
                                ("Tesla Model Y 2023", "Honda Accord 2014", "Toyota Camry 2021"),
                            )
                        LossDate=st.text_input("What is the Date and time of the Incident, provide this in YYYY-MM-DD HH:mm format","2024-08-06 13:15")
                        LossLocation=st.text_input("As close as you can recall, Where did it happen? (City , Zip,  or address)","43015")
                        Details=st.text_input("Describe the incident as best as you can","While I was driving ....")
                        DriverName=st.text_input("Can you provide full name of the person who was driving the car?","DJ")
                        IncidentReport=st.text_input("If you have a Police Incident report number, please enter that. If not say I dont know or Not applicable","NA")

                        if st.button("Initiate the Claim process"):
                            
                            table = dynamodb.Table(DDBtableNewClaim)
                            response = table.update_item(
                                Key={
                                    'CaseNumber': PolicyVinNumber+"-"+str(otptoken)
                                    },
                                    UpdateExpression="set VerifyCustomerMessage=:a ,CustomerName=:b,CustomerEmail=:c ,CustomerPhone=:d,CarMake_Model=:e ,LossDate=:f,LossLocation=:g,Details=:h,IncidentReport=:i,DriverName=:j,case_status=:k,VehiclceAnalysis=:l",
                                    ExpressionAttributeValues={
                                        ':a': "Mobile",
                                        ':b': CustomerName,
                                        ':c': CustomerEmail,
                                        ':d': CustomerPhone,
                                        ':e': CarMake_Model,
                                        ':f': LossDate,  
                                        ':g': LossLocation,
                                        ':h': Details,
                                        ':i': IncidentReport,  
                                        ':j': DriverName,
                                        ':l': {},
                                        ':k': "Pending for user documents"

                                    },
                                    ReturnValues="UPDATED_NEW"
                            )
                            st.write("A new case is opened for you, please note down the case # "+PolicyVinNumber+"-"+str(otptoken))                   
                except:
                    st.write("We are not able to verify the OTP, please re-enter the OTP")               
        else:
            st.write("We are not able to find a matching record, please renter the Policy Number")

    except:
        st.write("We are not able to find a matching record, please renter a valid Policy Number")


