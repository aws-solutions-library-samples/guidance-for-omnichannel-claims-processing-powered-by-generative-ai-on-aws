# Guidance for Omnichannel Claims Processing Powered by Generative AI on AWS

This repository contains guidance for implementing generative AI powered claims processing using Amazon Bedrock. This claims processing solution using generative AI leverages advanced AI capabilities to streamline, automate, and enhance the efficiency of the claims management process. This guidance provides step by step instructions for implementing First notice of loss (FNOL) solution to streamline auto insurance claims handling process, improve customer experience, and enhance the accuracy and efficiency of claims processing, including detecting and preventing fraudulent claims.

## Table of Contents

1. [Overview](#overview)
   - [Cost](#cost)
   - [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
   - [Operating System](#operating-system)
   - [AWS account requirements](#aws-account-requirements)
3. [Deployment Steps](#deployment-steps)
4. [Deployment Validation](#deployment-validation)
5. [Running the Guidance](#running-the-guidance)
6. [Next Steps](#next-steps)
7. [Cleanup](#cleanup)
8. [Things to know](#things-to-know)
9. [Revisions](#revisions)
10. [Notices](#notices)
11. [License](#license)
12. [Authors](#authors)

## Overview

### Use Case Description:

Claims processing solutions using Generative AI (Gen AI) leverage advanced AI capabilities to streamline, automate, and enhance the efficiency of the claims management process. This section outlines different use-cases or capabilities within claims processing:


1. Automated Claims Triage: Automatically classify incoming claims based on their severity, complexity, and priority. Reducing the initial assessment effort  and routing to the appropriate resource for further action.
2. Fraud Detection and Prevention: Analyze patterns in claims data to detect and prevent fraudulent activities. By using machine learning algorithms, identify anomalies and suspicious behaviors such as inflated or duplicate claims submissions for the same incident. 
3. Damage Assessment through Computer Vision: Use computer vision AI to assess damage in auto insurance claims. Analyze the images submitted by claimant, estimate the repair costs, and provide a detailed report, significantly speeding up the damage assessment process and improving accuracy. 
4. Document Analysis & Summarization : Employ NLP to extract & summarize relevant information from unstructured documents like medical records, police reports, and claim forms, helping in validation of claims by cross-referencing extracted data with policy details and identifying any discrepancies. 
5. Automating Customer interaction : Improve customer interactions, and capture and analyze claims, by deploying access to new digital channels that span portals, mobile applications, call centers, chatbots, and voice.
6. Policy Compliance and Regulatory Reporting: Automate the monitoring and reporting of claims-related activities to ensure compliance.
7. Predictive Analytics for Claims Forecasting: Utilize AI to predict future claims trends and assess potential risks.

This guidance package focuses on streamline the claims handling process, providing omnichannel customer experience, and enhance the accuracy and efficiency of claims processing, including detecting and preventing fraudulent claims.

### High-Level process flow

![Claims Processing on process flow](source/Assets/FSI_Claims_Processing_process_flow.png)

- Leverage omni-channel FNOL (First Notice of Loss) submission process that enables customers with multiple convenient options (chatbot, SMS, mobile-app, call, email, or a web form) to seamlessly submit their claims
- Automate document data extraction and claims case preparation using Amazon Textract , Amazon Comprehend, Amazon Bedrock, etc
- Reduce fraud risk and false positives using Amazon Bedrock, Amazon SageMaker and graph databases like Amazon Neptune
- Automate loss determination and cost of claim using AWS AI/ML and Gen AI Services
- Automate data collection and increase speed to decision using AWS AI/ML and Gen AI Services
- Automate claims fulfillment and omnichannel customer communication


### Key personas

The key personas involved in claims processing in the insurance industry include claims adjusters/examiners, claims managers, customer service representatives, underwriters, fraud investigators, systems analysts, compliance officers, and data scientists/engineers.

### Target partners/customers
The target partners/customers come from various sectors within the insurance industry, such as health insurers, property and casualty (P&C) insurers, life insurers, third-party administrators (TPAs), legal firms, self-insured corporations, government agencies, and reinsurance companies.

### Architecture

![Claims Processing on AWS Architecture](source/Assets/FSI_Claims_Processing_Architecture.png)

The above image represents an architecture that leverages various AWS services and generative AI capabilities to streamline the claims processing workflow, including:


1. Amazon CloudFront serves the Claims Processing React Web Application including Amazon Connect Chat interface. Amazon Cognito and AWS WAF protects Amazon CloudFront.

2. Initiates First Notice of Loss (FNOL) communication via call, SMS & chat using Amazon Connect and Amazon Lex and webform using Claims Processing Web Application. 

3. Stores claims request details in an Amazon DynamoDB table. 

4. Claims documents uploaded via Claims Processing Web Application is stored in Amazon Simple Storage Service (Amazon S3). S3 events trigger an AWS Lambda which invokes Amazon Textract to analyze documents such as driver’s license and invokes Amazon Nova Pro LLM using Amazon Bedrock to analyze images of vehicle damages. AWS Lambda updates the generated insights including potential cost to replace and repair the coverable to existing claims record in the Amazon DynamoDB table.

5. API Gateway and AWS Lambda integrates 3rd party application data to Claims Processing Web Application.

6. Adjuster leverages Amazon Bedrock Knowledgebase to search information via Amazon API Gateway and AWS Lambda. Amazon S3 stores knowledge articles for the Amazon Bedrock knowledge base. Amazon OpenSearch Serverless is used as the Vector database.

7. Adjuster reviews and adjudicates the claim request using the web application. 

8. Adjuster decision is sent to Amazon Simple Queue Service (Amazon SQS) queue. 

9. AWS Lambda picks the messages from Amazon SQS and notifies the claimant the status of the claim request via Amazon Connect.

10. AWS Lambda in a VPC picks the messages from Amazon SQS and updates 3rd party applications such as [Stripe](https://stripe.com/), [Guidewire](https://www.guidewire.com/), [Socotra](https://www.socotra.com/), etc for further downstream processing (if required).



## Cost

### Sample Cost Table

The following table provides a sample cost breakdown for trying out this guidance package with the default parameters in the US East (N. Virginia) Region. While you try out, we assume you initiate ~10 claims, send 20 SMS and have 100 chat messages.

| Description | Service |  Cost [USD] | Configuration summary |
|-------------|----------|--------------|-------------------------|
|Customer Experience |Amazon Connect - SMS/Chat Cost|$0.72|Amazon Connect charges for 20 SMS (@0.01/SMS) and 100 chat messages(@0.040/message) with 2 TFN (@0.06/day)|
|Orchestration, Integration |AWS Lambda|$0.00| Free Tier ~ 5 API calls per claim and is covered as part of Free Tier.|
|Integration |Amazon API Gateway |$0.00| 1000 REST API requests/month|
|AI/ML - Document extraction |Amazon Textract |$0.02| Extract and Analysis of 1 page (Driver's license) per claim @ $.02 per page|
|Generative AI - Image Processing | Amazon Bedrock |$2.88| Anthropic Claude 3 Haiku model used for damage assessment & summarization of images. Key assumptions - 1 image per claim , image format jpeg , 1 Mega pixel , 1 MB. ~1500 input tokens and 2000 output tokens|
|Generative AI - Knowledge assistance | Amazon Bedrock Knowledge bases (RAG)|$2.88| Amazon Claude Haiku model usage ~1500 input tokens and 2000 output tokens|
|Generative AI - Knowledge assistance | Open Search Serverless Vector DB |$1.20|$0.24 per OCU per hour each for Indexing & searching.$0.24 for storage. Priced for 2 OCUs|
|Notification and 3rd party integration | Amazon SQS |$0.00|Free Tier, ~ 20 messages and is covered under Free Tier|
|Datastore |Amazon DynamoDB |$0.25| On-demand pricing with default settings. 1GB storage max with 1 KB average item size / 4 KB = 0.25 unrounded read request units needed per item.|
|Datastore | Amazon S3 |$0.05| S3 Standard storage (2 GB per month @$0.022 per GB), GET, SELECT, and all other requests from S3 Standard (100), PUT, COPY, POST, LIST requests to S3 Standard (100).|
|Security |AWS Web Application Firewall |$6.00| 1 web ACL with 1 rules in it|
|Security |Amazon Cognito |$0.00| 10,000 MAU is part of free Tier|
|**Total** | - |$13.99|-|

More than 100 AWS products are available on AWS Free Tier today. Click [here](https://aws.amazon.com/free/) to explore our offers.

*Note: We recommend creating a [Budget](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) through [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) to help manage costs. Prices are subject to change. For full details, refer to the pricing webpage for each AWS service used in this Guidance. For the most current and detailed pricing information for Amazon Bedrock, please refer to the [Amazon Bedrock Pricing Page](https://aws.amazon.com/bedrock/pricing/).*


## Prerequisites

This prototype uses AWS Customer Experience Services, such as Amazon Lex and Amazon Connect. You need administrative experience to set up customer engagement channels via those AWS services for this prototype to work. More details about setting up those services can be found under `Deployment Steps` section below.

This prototype leverages Amazon Connect [Two-way SMS feature](https://docs.aws.amazon.com/sms-voice/latest/userguide/two-way-sms-phone-number.html) and it requires a phone number to be claimed in [AWS End User Messaging](https://aws.amazon.com/end-user-messaging/) service. This requires [registration process](https://docs.aws.amazon.com/sms-voice/latest/userguide/registrations-create.html) and can take more than 15 days. So it is advised to test this solution in a non-production environment where you have an SMS phone number approved to be used. If you have [End User messaging](https://aws.amazon.com/end-user-messaging/) and an SMS  configured to send messages to your number, you will recieve the OTP and final notification. If you dont have it configured or get an error message saying "Not able to send message", yo can use the sample OTP 999999 as temporory workaround for testing purpose. 

### Operating System

Deployment using Integrated Development Environment (IDE) or local enviornment may require additional steps such as configuring [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) and [python](https://www.python.org/about/gettingstarted/) detailed under [Tools](#Tools).

Before deploying the guidance code, ensure that the following required tools have been installed in your IDE:

- [AWS Cloud Development Kit (CDK) >= 2.126.0](https://aws.amazon.com/cdk/)
- [Python >= 3.9](https://www.python.org/downloads/release/python-390/)
- [AWS CLI v2](https://aws.amazon.com/cli/)
- To set up Amazon Bedrock Knoledgebase through CDK, we use `generative-ai-cdk-constructs`, a custom library (https://github.com/awslabs/generative-ai-cdk-constructs/blob/main/src/cdk-lib/bedrock/README.md) and it needs [Docker](https://docs.docker.com/engine/install/) to be running on your IDE. 
- [Docker](https://docs.docker.com/get-started/get-docker/) installed
   - Note: [buildx](https://github.com/docker/buildx) is also required. For Windows and macOS buildx is included in [Docker Desktop](https://docs.docker.com/desktop/)
   
### AWS account requirements

**Required resources:**

- [Bedrock Model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
   - Claude 3 models 
      - Haiku 3 for vehicle image analaysis - anthropic.claude-3-haiku-20240307-v1:0
      - Claude v2 (anthropic.claude-v2) and Claude v2.1 (anthropic.claude-v2:1) for Amazon Lex generative AI features
   - Amazon Models
      - Titan Text Embeddings for Knowledge assistance source document embedding - amazon.titan-embed-text-v2:0 or amazon.titan-embed-text-v1 
      - Amazon Nova Prod for vehicle image analaysis - amazon.nova-pro-v1:0 
- [Amazon S3](https://aws.amazon.com/s3/)
- [AWS Lambda](https://aws.amazon.com/lambda/)
- [Amazon DynamoDB](https://aws.amazon.com/dynamodb/)
- [Amazon SQS](https://aws.amazon.com/sqs/)
- [Amazon Textract](https://aws.amazon.com/textract/)
- [Amazon Lex](https://aws.amazon.com/lex/)
- [Amazon Connect](https://aws.amazon.com/lex/)
- [AWS End User Messaging](https://aws.amazon.com/end-user-messaging/)
- [Amazon Cognito](https://aws.amazon.com/cognito/)
- [AWS WAF](https://aws.amazon.com/waf/)
- [AWS IAM](https://aws.amazon.com/iam/)
- [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)


### Supported Regions

The guidance package is well suited to be deployed in `us-east-1` and `us-west-2` regions. However you can verify the availability of services listed in the architecture above (specifcally Amazon Bedrock, AWS End User Messaging, Amazon Connect and Amazon Lex) and opt a region where all those services are supported.

AWS WAF dependency: This is required because CloudFront WAF WebACLs must be created in us-east-1, regardless of where your main application stack is deployed. If deploying this stack in a region other than us-east-1:
1. Create a separate stack for the WAF WebACL in us-east-1
2. Deploy the WAF stack separately before deploying this main stack
3. Update the CloudFront distribution to use the WAF WebACL ARN from us-east-1

### AWS CDK

This Guidance uses AWS CDK. If you are using aws-cdk for the first time, please see the [Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) section of the AWS Cloud Development Kit (AWS CDK) v2 developer guide to learn about AWS CDK.

## Deployment Steps

### 1. Requesting Access to AWS Bedrock

1. Log in to the AWS Management Console
2. Search for "Bedrock" in the search bar
3. In the left navigation pane, under Bedrock configurations, choose Model access.
4. On the Model access page, choose Enable specific models.
5. Select the following models from the list: 
   - Claude 3 models - Haiku 3 and Claude
   - Amazon Titan Text Embeddings 
   - Amazon Nova Pro
6. Scroll down to the bottom of the screen, click Next
7. Click "Submit" button. 

You will see the model access request with an in progress status. Getting access to the model and that change to be reflected in the console can take several minutes.

### 2. Set up and verify customer experience services 

If you have an existing Amazon Connect instance and wanted to use that instance, SKIP the instance creation step below and follow the steps to import the contact Flow (step 2). 
   
   1. To set up Amazon Connect instance, follow the insutructions [set up your Amazon Connect instance](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-instances.html)

   2. [Import the sample contact flow](https://docs.aws.amazon.com/connect/latest/adminguide/contact-flow-import-export.html#how-to-import-export-contact-flows) `GP-FSI-ClaimsProcessing.json` given under `source/AmazonConnect/ContactFlow`
      Log in to your Amazon Connect instance. The account must be assigned a security profile that includes edit permissions for flows.
      - Log in to your Amazon Connect instance.
      - On the navigation menu, choose `Routing`,  `Flows`.
      - Click on 'Create flow'
      - Select `Import (beta)` option under the drop down next to 'Save'
      - 'Choose` the file (GP-FSI-ClaimsProcessing.json) to import 
      - Once we deploy the stack and have the Amazon Lex chatbot and AWS Lambda added to your connect instance, we will review and update any resolved or unresolved references as necessary prior we `Save and Publish` the flow (instructions given under `Amazon Connect Changes Contact Flow changes` of `Make updates based on CDK resources` section).

To set up a phone numer with Amazon Connect two way SMS enabled, follow the insutructions below:

   3. [Claim a phone number with two way SMS in Amazon Connect](https://docs.aws.amazon.com/connect/latest/adminguide/setup-sms-messaging.html)

   4. [Map the two-way phone number](https://docs.aws.amazon.com/connect/latest/adminguide/associate-claimed-ported-phone-number-to-flow.html) to the `GP-FSI-ClaimsProcessing` contact flow.
   
   5. Set up Amazon Connect chat user interface in your react App (use the file `MainPage.tsx`)
    - You can add Amazon Connect chat user interface to a webpage by configuring the communications widget in the Amazon Connect admin website as detailed [here](https://docs.aws.amazon.com/connect/latest/adminguide/add-chat-to-website.html). While configring the communications widget, in the Communications options section, choose `Chat` option for your customers to engage with your widget (you can ignore `Web calling`), and then choose Save and continue. 
      - You can select the Contact Flow `GP-FSI-ClaimsProcessing` created earlier
      - For the option to `Add security for your communications widget`, you can opt `No` 

         Note: To add security for your chat communications widget to have more control when initiating new chats, including the ability to verify that chat requests sent to Amazon Connect are from authenticated users, you can follow [this documentation ](https://docs.aws.amazon.com/connect/latest/adminguide/add-chat-to-website.html#confirm-and-copy-chat-widget-script)
      - COPY and Paste the `Communications widget script` into line 28-38 in the `MainPage.tsx` file kept under `source/ReactApp/src/pages` using your IDE

### 2. CDK deployment

   1. Clone the code repository. In your IDE, use the terminal to clone the repository:

       ```
       git clone https://github.com/aws-solutions-library-samples/guidance-for-omnichannel-claims-processing-powered-by-generative-ai-on-aws.git
       ```

   2. Navigate to the folder: guidance-for-omnichannel-claims-processing-powered-by-generative-ai-on-aws using in yout IDE
       ```
       cd guidance-for-omnichannel-claims-processing-powered-by-generative-ai-on-aws
       ```
   3. Make changes to the default values given.

      - The file named  `deploy.sh` takes care of deploying CDK stacks and deploying other necessary resources. You can edit this file to update the default/sample values provided:
         - SMS_Origination_number_ARN - ARN of the SMS number claimed via [Amazon Connect with SMS feature enabled](https://docs.aws.amazon.com/connect/latest/adminguide/setup-sms-messaging.html#get-sms-number)
         - CustomerPhone with a valid phone number to send/recieve SMS (eg: your cell number)   
         - if you have wanted to integrate with [Socotra](https://www.socotra.com/) insurance platform, then update these values
            - SOCOTRA_ENDPOINT, SOCOTRA_HOST, SOCOTRA_USERNAME, SOCOTRA_PASSWORD
            - SOCOTRA_External_PolicyHolderId1/2/3/4 with some some sample policy holder IDs
         - if you have wanted to integrate with [Guidewire](https://www.guidewire.com/) claims platform, then update these values
            - GW_USERNAME, GW_PASSWORD and GW_BASE_URL (eg: https://xxxxx.guidewire.net:443/rest)
         - If you have [Stripe](https://stripe.com/) payment processing integration to be enabled, updadate REACT_APP_STRIPE_PUBLISH_KEY with the [Stripe Publishable API key](https://docs.stripe.com/keys)

   4. **Run** the file named `deploy.sh` passing the target region as an input parameter
      ```
       sh deploy.sh <AWS Region>
       ```
       Example: sh deploy.sh us-east-1

      The `deploy.sh` file on this folder will do the following things:
        1. This project is a Python Project. Commands to switch to the Virtual Env, activate virtual env and install the required dependencies in the virtual environment.
        2. Initialize CDK within the project using the command: ```cdk init```
        3. Bootstrap the CDK environment using the command :```cdk bootstrap```
        4. Verify that the CDK deployment correctly synthesizes the CloudFormation template:```cdk synth```
        5. Deploy the Backend Components running the following command: ```cdk deploy```
    
      **Note**:

         Running `deploy.sh` file will deploy a stack named `ClaimsProcessingStack1`.

         File named `loadsamples.py` is used for loading sample data to dynamodb tables. You can edit the sample dataset by editing `claimsprocessing/loadsampledata.py`. Also, the same file is used for importing a sample Amazon Lex chatbot, buidling it and makeing sure the alias has the `gp-fsi-claimprocessing-filenewclaim` Lambda associated as the Lambda codehook.

         You can change the resource names by editing the enviornment variables set in the `deploy.sh` file.
      
      It will take approximately *10 minutes* to deploy the entire stack. 

      Note: If you wanted to deploy this CDK stack to more than one region in a single AWS account, you need to change the resource names to have the region post-fixed so that the stack execution won't throw the `resource exists` error.


   ### Deployment Validation
    
   1. Verify a successful deployment of the CDK stack and CloudFormation stacks:
      - Open [CloudFormation](https://console.aws.amazon.com/cloudformation/home) console 
      - Verify that the status of the stacks named `ClaimsProcessingStack1` is `CREATE_COMPLETE`
      - You can click on `resources` tab of the stack which shows all the resources created by the stack.

   2. Check Amazon dynamodb tables and sample data:
      - Open the Amazon DynamoDB console
      - Go to `Tables`
      - Check for tables with the name GP-FSI-ClaimsProcessing-* 
      - Click on tables and click on Exmplore table items. Except GP-FSI-ClaimsProcessing-NewClaim table, you should see data in rest of the tables.

   3. Verify that an Amazon Lex bot is imported:
      - [Open the Amazon Lex console](https://console.aws.amazon.com/lex/).
      - You should see an Amazon Lex bot named `GP-FSI-Claims-Processing`

   4. Verify that the Amazon Bedrock Knowldgebase is created: 
      - [Open the Amazon Bedrock console](https://console.aws.amazon.com/bedrock/).
      - Go to `Builder tools` in the left pane by expand the burdger icon, click `Knowledge bases`
      - Click the one named `gp-fsi-claims-processing-knowledge-base`
      - Click the "Data source name" under `Data source`section
      - Check the `Sync history` with status `Complete` and `Source files` count as 1

   - If there are errors while running the python scripts, it will give error details that you can check and resolve

### 3. Make updates based on CDK resources

   1. Informational: A sample Amazon Lex will be created by the Stack using the file named `loadsamples.py` under `claimsprocessing` folder. It will import a sample bot, buid it and creates an alias with `gp-fsi-claimprocessing-filenewclaim` Lambda associated for the Lambda codehook. The sample Amazon Lex `GP-FSI-ClaimsProcessing-sample.zip` shared as part of this guidance package is imported.
   
   If needed, you can manually import the sample Amazon Lex following [this](https://docs.aws.amazon.com/lex/latest/dg/export-to-lex.html) or given below :
      - Download `GP-FSI-ClaimsProcessing-sample.zip` given under the path `source/Amazon Lex` 
      - Using Amazon Lex console, under `Actions` use the `Import` opion to [import the Zip file to create the bot](https://docs.aws.amazon.com/lexv2/latest/dg/import.html)
      - Select the bot and [build the bot](https://docs.aws.amazon.com/lexv2/latest/dg/building-bots.html) (Go to Versions -> All languages -> Language: English (US)), click `build` 
      - [Deploy the bot](https://docs.aws.amazon.com/lexv2/latest/dg/deploying.html) - create a version of the latest build and create an alias with the latest version of the bot 

   2. Amazon Connect Changes Contact Flow changes

      - [Add the Amazon Lex bot created/imported to the Amazon Connect instance](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-lex.html). The Lex bot is named "GP-FSI-Claims-Processing"
      - Update Contact Flow imported: update `Get customer input` with the Lex chatbot details, and select a `queue` and publish the flow. You can make further changes to the Amazon Connect contact flow based on Amazon Lex intents if you prefer.

   3. Allowlist the Amazon CloudFront URL in your Amazon Connect chat widget
      - Get the `CloudFrontURL` from the output of `ClaimsProcessingStack1` stack (CloudFront URL)
      - Add it as an approved domain to your Amazon Connect communication widget as instructed [here](https://docs.aws.amazon.com/connect/latest/adminguide/add-chat-to-website.html#chat-widget-domains)

   3. Use the sample Cognito User created or set up Cognito User

      #### Use the sample Cognito User created
       - As part of the deployment, using `loadsamples.py` file, we create a sample coginot user with email "test@example.com" and temporary_password "Test@1234". - When you login to the Amazon CloudFront URL, you will be prompted to reset the password to a new one. 

      #### Set up Cognito User
      - Go to the Amazon Cognito console . If prompted, enter your AWS credentials.
      - Navigate to user pools on the left side of the panel. You should see a user pool created via CDK stack.
      - Click on the pre-created user pool. You will land on the image shown below:
      - Click on Users tab below Getting Started section and click on create user to create your user profile.
      - Now, create a new user by providing username, valid email address and temporary password to login to the application.
      - After this setup, you should be able to login and launch your application!

   5. Informational: An Amazon Bedrock Knowledgebase named `GP-FSI-ClaimsProcessing` will be created by the stack and Amazon Bedrock knowledgebase sync job will be run by `loadsamples.py`. However, below given the instructions to create Amazon Bedrock Knowledgebase manually from AWS console if needed:
   
      - Navigate to Amazon Bedrock Knowledge base in AWS console 
      - Provide a knowledge base name.
      - Further, provide the S3 URI of the object containing the files for the data source that got created as part of the stack deployment, that is, select the S3 as data source to your Knowledge base setup that got created due to CDK deployment.
      - For this, click `browse s3` and select bucket starting with the name - `claimsprocessing-<account name>`. Some sample knowledgebase articles are stored under 'Knowledgebase' folder in that S3 bucket.
      - Next, you can keep the chunking strategy as "default", select `Titan Text Embeddings v2` model to embed the information and select `Quick create a new vector store` in order to have default option for the vector DB when creating the knowledge base. Note that Knowledge Base can take approximately 10 minutes to be created.
      - Take note of the `knowledge base ID` once the knowledge base has been created. If you do this manually, this value needs to be added/updated to the DynamoDB table named `GP-FSI-ClaimsProcessing-FM`. 
      - [Refer](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-create.html) to create your own Bedrock Knowledge Base with Opensearch serverless vector DB in your account.

## Submit FNOL

### Via Webform 

  1. Go to CloudFormation stacks, open `CloudFrontURL` given in the `Outputs` tab of `ClaimsProcessingStack1`.
  2. The URL will prompt you for the login and you can use the Amazon Congito user credentials set earlier
  3. In the 'Initiate a new claim', you can enter your policy number (eg: PY1234)
  4. If you have Amazon Connect SMS configured to send messages to your number, you will recieve the one time password (OTP) and final notification. If you dont have SMS feature configured, as a workaround, you can use the sample OTP 999999.
  5. Enter the OTP and once verified, you will be given option to enter the details of the incident.
  6. Once you have the details filled, **click** the `Submit` button and a case will be opened. Make a note of the Case number (policy number+OTP). 

### Via Chatbot

 1. Go to CloudFormation stacks, open `CloudFrontURL` given in the `Outputs` tab of `ClaimsProcessingStack1`.
 2. Once authenticated, you will see a chatbot icon at the bottom right. 
 3. While interacting with the chatbot, you will be prompted to enter the OTP for authentication. If you have the SMS feature configured to send messages to your number, you will recieve the one time password (OTP). If you dont have it configured, you can enter "999999" as an OTP as a workaround.
 
 Note: To add security for your chat communications widget to have more control when initiating new chats, including the ability to verify that chat requests sent to Amazon Connect are from authenticated users, you can follow [this documentation ](https://docs.aws.amazon.com/connect/latest/adminguide/add-chat-to-website.html#confirm-and-copy-chat-widget-script).

### Via SMS

1. To the Amazon Connect two way SMS phone mapped to the `GP-FSI-ClaimsProcessing` contact flow, send a sample SMS (eg: Hi) and the two way SMS conversation will start.

## Upload supporting documents
  - Using the case id, you can upload the supporting documents via `Upload Documents` page of the web app.
  - You will be promoted to upload your drivers license and accident images. For the drivers license, you can use the sample file named `DLRegular.png` kept under `source/Assets`. Once you select the file, remeber to click on the Upload button. Once you click the upload button, you will see a message saying `File Successfully Uploaded`
  - Once the images are uploaded, the document validation and image analysis will take place and the results will be updated to `GP-FSI-ClaimsProcessing-NewClaim` DynamoDB table by `gp-fsi-claimprocessing-docprocessor` Lambda. So if you see the results are not getting updated, check the Cloudwatch logs for this Lambda to identify if there are any issues.
  - Amazon Bedrock Converse API is used in the backend code to make API calls. This API provides a consistent interface that works with all models that support messages. You can read more about Amazon Bedrock Converse API from [link 1](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html) and [link 2](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse.html#)
 
## Adjudicate the claims
  -   For Agents to validate the supporting documents and adjudicate, use the `Adjuster` page of the web app.
  -   In the main pane, agent can see all tickets and see the status and choose the tickets to review.
  -   For those selected tickets, agents will get details around the Drivers linces validation and image analysis completed.
  -   Using those, agent can take a decision to approve/reject or ask for more details
  -   Once agent click the submit button, the decison will be recorded in the `GP-FSI-ClaimsProcessing-NewClaim` tables and a message will be send to the customer (provided SMS feature is configured)

## GenAIAssistant
- Using 'GenAIAssistant' page, adjuster can ask questions and get answers that is powered by Bedrock knowledge bases. For example, the can ask `What is the Average Collision Repair Cost?`
- Adjuster will be able to select different LLM models

## External Claims System Integration
   - Using `External Claims System Integration` tab, adjuster can view policyholders information from 3rd Party Claims Systems such as Socotra, Guidewire, etc. 
   - For the DEMO purpose, we have the API integration enabled for Socotra and Guidewire. This page will work if you have the Claims system credentials updated as the enviornment variables in the `deploy.sh` file.

Note: To potentially achieve more accurate or tailored results, we encourage you to experiment with editing the prompts you provide to the model (edit the prompts given in `GP-FSI-ClaimsProcessing-FM` DynamoDB table). By modifying the prompts, you can often guide the model to generate outputs that are more closely aligned with your requirements.

## Next Steps

Here are some suggestions and recommendations on how customers can modify the parameters and components of the Claims Processing application to further enhance it according to their requirements:

1. **Customization of the User Interface (UI)**:
   - Customers can customize the frontend to match their branding and design requirements.
   - They can modify the layout, color scheme, and overall aesthetic of the application to provide a seamless and visually appealing experience for their users.
   - Customers can also integrate the application with their existing web or mobile platforms to provide a more cohesive user experience.

2. **Expansion of the Knowledge Base**:
   - Customers can expand the knowledge base by ingesting additional data sources for claims processing.
   - This can help improve the quality and relevance of the accident image analysis provided by the application.
   - Customers can also explore incorporating user feedback and interactions to continuously refine and update the knowledge base.

3. **Integration with External Data Sources**:
   - Customers can integrate the application with additional data sources, such as ERP, CRM systems or vehicle data systems.
   - This can enable more comprehensive and context-aware analysis, taking into account factors like vehicle parts pricings, existing claims history, etc.

4. **Advanced Analytics and Reporting**:
   - Customers can integrate the application with business intelligence and analytics tools to gain deeper insights into user behavior, recommendation performance, and overall application usage.
   - This can help customers make data-driven decisions to further optimize the Claims Processing and better align it with their business objectives.
   
5. **Integration with other Applications or Solutions**:
   - Customers can integrate the application with External Applications or Solutions for various use cases for claims processing.
   - For example: you can use an AWS partners for claims management, data analysis,  or claims prediction, etc


By exploring these next steps, customers can tailor the Claims Processing application to their specific needs, enhance the user experience, and unlock new opportunities for growth and innovation within their FSI Claims processing businesses.

## Cleanup

### Cleanup of CDK-Deployed Resources

1. **Terminate the CDK app**:
   - Navigate to the CDK app directory in your Cloud9 terminal. In your case, go to the git repo
   - Run the clean up script  `sh destroy.sh <aws-region>`  eg: `sh destroy.sh us-east-1`
   - This should Amazon Lex imported, delete the CDK stacks and related resources

2. **Verify resource deletion**:
   - Log in to the AWS Management Console and navigate to the relevant services to ensure all the resources have been successfully deleted.

### Manual Cleanup of Additional Resources

1. **S3 Bucket Content**:
   - The Claims Processing application may use an S3 bucket to store generated images or other unstructured data.
   - If the S3 bucket was not managed by the CDK app, you will need to delete the contents of the bucket manually.
   - Log in to the AWS Management Console and navigate to the S3 service.
   - Locate the S3 bucket used by the application and delete all the objects within it.
   - Once the bucket is empty, you can delete the bucket itself.


## Things to know

- Please note that in this guidance package, we used a sample react application servred to end users via Amazon Cloudfront distribution. Customer can opt their preferred web hosting/UI aproaches.

- Additionally, for this PoC guidance package, DynamoDB was used to store the metadata. You have the option to choose other datastores as well.

- For 3rd party Claims integration, we used Guidewire and Socotra. You can leverage the similiar integration approach to other claims systems or 3rd party solutions. 

- This prototype expects an SMS phone number registrted for testing. If you have [End User messaging](https://aws.amazon.com/end-user-messaging/) and an SMS  configured to send messages to your number, you will recieve the OTP and final notification. If you dont have it configured or get an error message saying "Not able to send message", yo can use the sample OTP 999999 as temporory workaround for testing purpose. 

## Revisions

All notable changes to the version of this guidance package will be documented and shared accordingly.

1. Nov 19, 2024 - Initial version of the guidance package
2. Feb 24, 2025 - Version 2 with the following changes:
   - UI changed from Streamlit to React. The UI uses [Cloudscape design](https://cloudscape.design/).
   - Changed the LLM model to Amazon Nova pro
   - Integration with [Stripe](https://stripe.com/)
   - Integration with [Guidewire](https://www.guidewire.com/)
   - Integration with [Socotra](https://www.socotra.com/)
   - Changed Amazon Pinpoint SMS to AWS End User Messaging SMS feature

## Notices

Customers are responsible for making their own independent assessment of the information in this Guidance. This Guidance: (a) is for informational purposes only, (b) represents AWS current product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. AWS responsibilities and liabilities to its customers are controlled by AWS agreements, and this Guidance is not part of, nor does it modify, any agreement between AWS and its customers.

Sample code, software libraries, command line tools, proofs of concept, templates, or other related technology are provided as AWS Content or Third-Party Content under the AWS Customer Agreement, or the relevant written agreement between you and AWS (whichever applies). You should not use this AWS Content or Third-Party Content in your production accounts, or on production or other critical data. You are responsible for testing, securing, and optimizing the AWS Content or Third-Party Content, such as sample code, as appropriate for production grade use based on your specific quality control practices and standards. Deploying AWS Content or Third-Party Content may incur AWS charges for creating or using AWS chargeable resources, such as running Amazon EC2 instances or using Amazon S3 storage.

Before deploying the provided code in a production scenario or use case, it is the responsibility of the customer to conduct thorough due diligence, including: 1. Security Threat Model - Perform a comprehensive threat modeling exercise to identify and mitigate potential security risks associated with the use case and architecture. 2. Static Code Analysis - Conduct an automated code review using the security tools to detect and address any vulnerabilities or security issues within the code. The security assessments performed as part of the Guidance package are meant to serve as a starting point. Customers/partners are solely responsible for ensuring the security and integrity of the code in their own production environments. AWS does not make any warranties or representations regarding the security or fitness for purpose of the provided code, and any use or deployment of the code is at the customer/partner's own risk. It is crucial that customers/partners perform their own independent security validations before deploying the code in a production scenario or use case.

The sample insurance company webpage for the chatbot interface uses a hard coded user name and password. You can modify the chatbot webui application to use your preferred authentication mechanisms. To add security for your Amazon Connect chat communications widget to have more control when initiating new chats, follow [this documentation](https://docs.aws.amazon.com/connect/latest/adminguide/add-chat-to-website.html#confirm-and-copy-chat-widget-script). For the Claimsprocessing webpage built using Streamlit (hosted on AWS Fargate and served via Amazon CloudFront), you can add Amazon Congnito for additional authentication and authorization by referrencing [this](https://github.com/aws-samples/deploy-streamlit-app). For the Cloudfront web pages, you can enable [AWS WAF for added security](https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-features.html).

By modifying the generative AI prompt sample we have shared in this guidance, you can often guide the model to generate outputs that are more closely aligned with your requirements. You are responsible for testing, securing, and optimizing the usage of generative AI as appropriate for production grade use based on your specific quality control practices and standards.

Integrations to 3rd party systems is to show the art of possible. You can change the integration logic as you prefer.

## License
This library is licensed under the MIT-0 License. See the LICENSE file.

## Authors

- Afsaneh Eshghi
- Bala KP
- Cory Visi
- Dilin Joy
- Saynatan Biswas
- Steven Wong
