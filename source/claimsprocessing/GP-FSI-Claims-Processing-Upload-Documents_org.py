
import boto3
import streamlit as st
import time
from boto3.dynamodb.conditions import Key

st.set_page_config(page_title="FSI Claims Processing")

st.title('Upload Claims Documents')

bucket_name="replace_bucket_name"
region_name="replace_region_name"
DDBtableNewClaim="replace_DDBtableNewClaim"



CaseNumber=st.text_input("Enter your CaseNumber")

def dynamodb_getitem(CaseNumber):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DDBtableNewClaim)        
    response = table.get_item(
        Key={
                'CaseNumber': CaseNumber
            }
        )
    #st.write(response)
    try:
        item=response['Item']
        CustomerPhone = item['CustomerPhone']
        return True
    except:
        Message="We are not able to find a matching data. enter the case number again."
        st.write(Message)
        return False

def Reverse(lst):
   new_lst = lst[::-1]
   return new_lst

def uploadMP4ToS3(file, bucket, s3_file):
    s3 = boto3.client('s3',
        region_name=region_name)
    
    try:
        s3.upload_fileobj(file, bucket, s3_file)
        st.success('File Successfully Uploaded')
        return True
    except FileNotFoundError:
        #time.sleep(9)
        st.error('File not found.')
        return False     
      
if CaseNumber:
    if dynamodb_getitem(CaseNumber): 
        st.write("Upload supporting documents such as License, vehicle images, police incident report, medical report, etc")
        st.subheader("License")
        uploaded_license_file = st.file_uploader(label="Upload the front page of your license here")
        if uploaded_license_file:
            if st.button('Upload License doc'):
                filename=uploaded_license_file.name
                filename=filename.replace(" ","")
                #st.write(filename.replace(" ",""))
                key='upload/'+str(CaseNumber)+"/license-"+filename
                #st.write(key)
                with st.spinner('Uploading...'):
                    uploadMP4ToS3(uploaded_license_file,bucket_name,key)
            st.subheader("Vehicle images")
            uploaded_vehilce_files = st.file_uploader(label="Upload the vehicle images",accept_multiple_files=True)
            if uploaded_vehilce_files:
                count_of_vehicle_files=len(uploaded_vehilce_files)
                #st.write(uploaded_vehilce_files)
                uploaded_vehilce_files=Reverse(uploaded_vehilce_files)
                #st.write(uploaded_vehilce_files)
                if st.button('Upload Vehcile Docs'):
                    for uploaded_file in uploaded_vehilce_files:
                        filename=uploaded_file.name
                        filename=filename.replace(" ","")
                        #st.write(filename.replace(" ",""))
                        key='upload/'+str(CaseNumber)+"/vehicle"+str(count_of_vehicle_files)+"-"+filename
                        #st.write(key)
                        with st.spinner('Uploading files... wait for all the files to be uploaded, it can take upto a minute'):
                            uploadMP4ToS3(uploaded_file,bucket_name,key)
                            time.sleep(5)
                        count_of_vehicle_files=count_of_vehicle_files-1
            Incident_report=st.checkbox("Do you have a Police incident report to upload?")
            if Incident_report:
                st.subheader("Police incident report")
                uploaded_incident_files = st.file_uploader(label="Upload the police incident report",accept_multiple_files=True)
                if uploaded_incident_files:
                    if st.button('Upload Incident Reort'):
                        for uploaded_file in uploaded_incident_files:
                            #st.write(uploaded_file)
                            filename=uploaded_file.name
                            filename=filename.replace(" ","")
                            #st.write(filename.replace(" ",""))
                            key='upload/'+str(CaseNumber)+"/incidentreport-"+filename
                            #st.write(key)
                            with st.spinner('Uploading...'):
                                uploadMP4ToS3(uploaded_file,bucket_name,key)

            Medical_report=st.checkbox("Do you have a Medical report to upload?")
            if Medical_report:
                st.subheader("Medical report")  
                uploaded_medical_files = st.file_uploader(label="Upload the medical report",accept_multiple_files=True)
                if uploaded_medical_files:
                    if st.button('Upload Medical Report'):
                        for uploaded_file in uploaded_medical_files:
                            #st.write(uploaded_file)
                            filename=uploaded_file.name
                            filename=filename.replace(" ","")
                            #st.write(filename.replace(" ",""))
                            key='upload/'+str(CaseNumber)+"/medical-report"+filename
                            #st.write(key)
                            with st.spinner('Uploading...'):
                                uploadMP4ToS3(uploaded_file,bucket_name,key)     
        else:
            st.write("You need to upload your license details to proceed")   
    else:
        st.write("Not able to validate your input details, please re-enter valid inputs")