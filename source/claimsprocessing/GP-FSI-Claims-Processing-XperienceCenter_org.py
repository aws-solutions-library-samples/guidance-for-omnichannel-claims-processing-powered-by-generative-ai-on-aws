
import json
import requests
import boto3
import streamlit as st
import time
from boto3.dynamodb.conditions import Key
import pandas as pd
import s3fs

sqs = boto3.client('sqs')
st.set_page_config(page_title="FSI Claims Processing")

st.title('Adjuster View')
dynamodb = boto3.resource('dynamodb')


bucket_name="replace_bucket_name"
account_id="replace_account_id"
region_name="replace_region_name"
DDBtableNewClaim="replace_DDBtableNewClaim"
DDBtableFM="replace_DDBtableFM"
QueueUrl="replace_QueueUrl"

table = dynamodb.Table(DDBtableNewClaim)

with st.sidebar:
    with st.expander("Would you like to use the adjuster assistance"):
        st.title('Adjuster Assistant')

#        txt = st.text_area('Enter your Claims questions here', """Eg1: What is the Average Collision Repair Cost? \nEg2: Does the company have to pay for original equipment manufacturer (OEM) parts?""")
        txt = st.text_area('Enter your Claims questions here', """What is the Average Collision Repair cost""")

        def getFMModel():
            table = dynamodb.Table(DDBtableFM)
            response = table.get_item(
                Key={'Active': 'Y'}
                )
            FMModeldata=response['Item']
            #print(FMModeldata)
            knowledgeBaseId=FMModeldata['knowledgeBaseId']
            model_id=FMModeldata['model_id']
            region_id=FMModeldata['region_id']
            api_url=FMModeldata['api_url']
            return knowledgeBaseId,model_id,region_id,api_url

        if st.button('Submit'):
            data_genai_res = st.text("Generating gen AI response, please wait...")      
            knowledgeBaseId,model_id,region_id,api_url=getFMModel()
            maxTokenCount= 512
            temperature= 0.00
            topP = 0.00
            api_url = api_url
            todo = {
            "prompt": "\n\nHuman: "+txt+"\n\nAssistant:",
            "model_id": model_id,
            "ds_kb":knowledgeBaseId,
            "textGenerationConfig": {
            "maxTokenCount": maxTokenCount,
            "temperature": temperature,
            "topP": topP
                }
                }
            response = requests.post(api_url, json=todo, timeout=180)
            print(response.raise_for_status())
            #st.write(response.text)
            data=response.text.replace("$","\$")
            data_genai_res.text("")
            st.write(data)



def fetch_all_data():
        response = table.scan()
        if response['Count']==0:
            st.write("No cases to show")
            exit()
        else:
            data=response['Items']
            #st.write(response)
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                data.extend(response['Items'])

            return data

def fetch_data(casestatus):
    response = table.query(
        IndexName='case_status-index',
        KeyConditionExpression=Key('case_status').eq('Review')
        )
    
    if response['Count']==0:
        data=""
    else:
        data=response['Items']
        #st.write(response)
    return data

# Streamlit app
def main():
    # Fetch data from DynamoDB table
    all_data = fetch_all_data ()
    # Convert data to pandas DataFrame
    df_all_data = pd.DataFrame(all_data)
    st.subheader("List of all Cases")
    df1_all_data=df_all_data[['CaseNumber','case_status','CustomerEmail','CustomerPhone','LossDate','LossLocation','CarMake_Model']]
    st.dataframe(df1_all_data, hide_index=True,use_container_width=True)
    casestatus='Review'
    data = fetch_data(casestatus)
    #st.write(data)
    if data=="":
        st.write("No cases to be reviewed")
    else:
        #test=True
        #if test:
        try:
            df = pd.DataFrame(data)
            #st.write(df)
            st.subheader("Cases to be reviewed")
            df1=df[['CaseNumber','CustomerEmail','CustomerPhone','LossDate','LossLocation','CarMake_Model']]
        
            # Display data as pandas DataFrame
            #st.dataframe(df1)
        
            selection = st.dataframe(df1, on_select="rerun", selection_mode="single-row", hide_index=True,use_container_width=True)
            #st.write(selection)
        
            row=selection['selection']['rows'][0]
            #st.write("You selected row:", row)
            CaseNumber=df[['CaseNumber']].iloc[row][0]
            #st.write(CaseNumber)
            dataselected=df.iloc[row]
            #st.write(dataselected)
            VehiclceAnalysis=df['VehiclceAnalysis'].iloc[row]
            Combined_vehicle_image_analysis_output=df['Combined_vehicle_image_analysis_output'].iloc[row]       
            License_vaidate=df['License_vaidate'].iloc[row]
            if CaseNumber:
                st.divider()
                if License_vaidate:
                    with st.expander("Expand this to see License Validation Results"):
                        st.subheader("**License Validation Results**")
                        st.write(License_vaidate.split(";")[0])
                        st.write(License_vaidate.split(";")[1])
                #try:
                with st.expander("Expand this to see Vehicle Images and Analysis"):
                    st.subheader("**Vehicle Images and Analysis**")
                    #st.write(VehiclceAnalysis)
                    fs = s3fs.S3FileSystem(anon=False)
                    for key, value in VehiclceAnalysis.items():
                        for key1, value1 in value.items():
                            st.image(fs.open(key1, mode='rb').read())
                            st.write(value1)
                    st.subheader("Combined Image Analysis")
                    st.write(Combined_vehicle_image_analysis_output)
                #except:
                    #st.write("Error to show Combined Image Analysis from S3 and DDB")
                    
                st.subheader("**Summary**")
                gen_ai_response=df[['GenAI_Summary']].iloc[row][0].replace("$","\$")
                st.write(gen_ai_response)
                st.divider()
                Decision = st.selectbox(
                    '**Approve** or **Reject** or **Pending,need more details**',
                    ('','Approve', 'Reject', 'Need more details'))
                AgentComments=st.text_input('Add Comments')
        
        
                ApprovedAmount=st.number_input('Enter the esitmated approved Claim amount',0,100000,500,250)  
                AgentComments=AgentComments+". The esitmated approved Claim amount is "+str(ApprovedAmount)  
                
                if st.button("Sumbit the decision"):
                    response = table.update_item(
                        Key={
                                            'CaseNumber': CaseNumber
                                            },
                                        UpdateExpression="set case_status=:m ,AgentComments=:c",
                                        ExpressionAttributeValues={
                                                ':m': Decision,
                                                ':c': AgentComments,
                                            },
                                            ReturnValues="UPDATED_NEW"
                                    )
                                
                    #st.write("Decision recorded to DB tbale")
                                                    
                
                    message="Decsion about your claim "+CaseNumber+" is "+Decision+". Agent comment - John:-"+AgentComments
                    # you can do a lookup to get the agent name dynamically.
                        
                    # Define the message body
                    message_body = CaseNumber+"-"+message
                        
                    # Send the message to the queue
                    response = sqs.send_message(
                                            QueueUrl=QueueUrl,
                                            MessageBody=message_body
                                        )
                    #st.write(response)    
                    # Print the message ID
                    #st.write(f'Message sent to the queue with ID: {response["MessageId"]}')
                                        
                    st.write("Notification is sent to the customer")
                    return response    

        except:
            pass





if __name__ == "__main__":
    main()


