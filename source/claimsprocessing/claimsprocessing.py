import platform
import os
import boto3
from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    aws_ecs as ecs,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_elasticloadbalancingv2 as elbv2,
    aws_s3_deployment as s3_deployment,
    aws_s3 as s3,
    aws_bedrock as bedrock,
    aws_sqs as sqs,
    aws_logs as logs,
    aws_lambda as lambda_,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda_event_sources as lambda_event_sources,
    aws_apigateway as apigateway,
    CfnOutput,
    aws_s3_notifications as s3n,
    aws_kms as kms,
    aws_opensearchserverless as opensearchserverless,
    aws_wafv2 as wafv2,

)

from aws_cdk.aws_ecr_assets import DockerImageAsset


class ClaimsProcessingStack1(Stack):


    def __init__(self, scope: Construct, construct_id: str, stack_variables: str = None,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
                   
        # Get the current account ID and region from the CDK context
        self.account_id = Stack.of(self).account
        self.region_id = Stack.of(self).region
        
        #print("Print stack1 variables")
        #print(stack_variables)
        # Define context variables
        self.DDBtableNewClaim=stack_variables['DDBtableNewClaim'][0]
        #print("DDBtableNewClaim", self.DDBtableNewClaim)
        self.DDBtableFM=stack_variables['DDBtableFM'][0]
        #print("DDBtableFM", self.DDBtableFM)
        self.DDBtableVehiclePricing=stack_variables['DDBtableVehiclePricing'][0]
        #print("DDBtableVehiclePricing", self.DDBtableVehiclePricing)
        self.DDBtableCustomerInfo=stack_variables['DDBtableCustomerInfo'][0]
        #print("DDBtableCustomerInfo", self.DDBtableCustomerInfo)
        self.Pinpoint_app_id=stack_variables['Pinpoint_app_id'][0]
        #print("Pinpoint_app_id", self.Pinpoint_app_id)
        self.Pinpoint_origination_number=stack_variables['Pinpoint_origination_number']
        #print("Pinpoint_origination_number", self.Pinpoint_origination_number)
        self.Pinpoint_origination_number=stack_variables['Pinpoint_origination_number']
        #print("Pinpoint_origination_number", self.Pinpoint_origination_number)
        self.bucketname=stack_variables['bucketname_input']+os.getenv('CDK_DEFAULT_ACCOUNT')
        BedrockKBID=stack_variables['BedrockKBID']
        #print(BedrockKBID)
        # Prefix for naming conventions
        prefix = "gp-fsi-claims-processing"
    
        
        """Generic permissions"""
        
        # Define the Bedrock policy statement
        self.bedrock_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:InvokeModel","bedrock:ListFoundationModels","bedrock:Retrieve","bedrock:RetrieveAndGenerate"],
            resources=[
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-v2:1",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-v2",
                #"arn:aws:bedrock:*:*:knowledge-base/"+BedrockKBID,  
                "arn:aws:bedrock:*:*:knowledge-base/*" #If you have a Knowledge base, you can comment out this line and provide the ID in the above line
            ]
        )

        
        self.pinpoint_policy_statement = iam.PolicyStatement(
                actions=[
                    "mobiletargeting:GetSmsChannel",
                    "mobiletargeting:SendMessages",
                    "mobiletargeting:PhoneNumberValidate"
                ],
                resources=[f"arn:aws:mobiletargeting:{self.region_id}:{self.account_id}:*"],
                effect=iam.Effect.ALLOW
            )
            

        """Generic Resources"""
        
        #create S3 bcuket for image processing
        self.s3_bucket = s3.Bucket(self, "GP-FSI-ClaimsProcessing", bucket_name=self.bucketname, versioned=True, removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True, enforce_ssl=True)
        

        
        self.s3bucket_policy_statement = iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                resources=[self.s3_bucket.bucket_arn, f"{self.s3_bucket.bucket_arn}/*"]
        )  
        
        
        '''
        # Specify the local directory containing the Knowledge base files
        local_asset_dir = os.path.join(os.getcwd(), "Knowledgebase/")
        print(local_asset_dir)

        # Deploy the files to the S3 bucket
        s3_deployment.BucketDeployment(
            self, "Knowledgebase",
            sources=[s3_deployment.Source.asset(local_asset_dir)],
            destination_bucket=self.s3_bucket,
            destination_key_prefix="Knowledgebase/"
            )
        '''
            
        # Define GP-FSI-ClaimsProcessing-FM dynamo DB for storing FM and prompt details 
        DDB_table_FM = dynamodb.Table(
            self, "GP-FSI-ClaimsProcessing-FM",
            table_name=self.DDBtableFM,
            partition_key=dynamodb.Attribute(name="Active",type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
            )
    
        
        
        # Define GP-FSI-ClaimsProcessing-VehiclePricing dynamo DB for storing sample vehicle prices
        DDB_table_VehiclePricing = dynamodb.Table(
            self, "GP-FSI-ClaimsProcessing-VehiclePricing",
            table_name=self.DDBtableVehiclePricing,
            partition_key=dynamodb.Attribute(name="CarMake_Model",type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
            )
        
            
           
        # Define GP-FSI-ClaimsProcessing-CustomerInfo dynamo DB for storing sample CustomerInfo       
        DDB_table_CustomerInfo = dynamodb.Table(
            self, "GP-FSI-ClaimsProcessing-CustomerInfo",
            table_name=self.DDBtableCustomerInfo,
            partition_key=dynamodb.Attribute(name="Policy_VIN",type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            )    
        DDB_table_CustomerInfo.add_global_secondary_index(
        partition_key=dynamodb.Attribute(name="CustomerEmail", type=dynamodb.AttributeType.STRING),
        index_name="CustomerEmail-index"
        )
        DDB_table_CustomerInfo.add_global_secondary_index(
        partition_key=dynamodb.Attribute(name="CustomerPhone", type=dynamodb.AttributeType.STRING),
        index_name="CustomerPhone-index"
        )
      

            
            
        # Define GP-FSI-ClaimsProcessing-NewClaim dynamo DB for storing customer FNOL and store the input data. 
        # This table is used as the master tables for agents to view the requests and approve it.   
        DDB_table_NewClaim = dynamodb.Table(
            self, "GP-FSI-ClaimsProcessing-NewClaim",
            table_name=self.DDBtableNewClaim,
            partition_key=dynamodb.Attribute(name="CaseNumber",type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
            )
        DDB_table_NewClaim.add_global_secondary_index(
        partition_key=dynamodb.Attribute(name="case_status", type=dynamodb.AttributeType.STRING),
        index_name="case_status-index"
        )
        DDB_table_NewClaim.add_global_secondary_index(
        partition_key=dynamodb.Attribute(name="CustomerEmail", type=dynamodb.AttributeType.STRING),
        index_name="CustomerEmail-index"
        )
        DDB_table_NewClaim.add_global_secondary_index(
        partition_key=dynamodb.Attribute(name="CustomerPhone", type=dynamodb.AttributeType.STRING),
        index_name="CustomerPhone-index"
        )  
        DDB_table_NewClaim.add_global_secondary_index(
        partition_key=dynamodb.Attribute(name="PolicyNumber", type=dynamodb.AttributeType.STRING),
        index_name="PolicyNumber-index"
        )   


        self.dynamodb_policy_statement =iam.PolicyStatement(
            actions=[
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem",
                "dynamodb:ConditionCheckItem",
                "dynamodb:PutItem",
                "dynamodb:DescribeTable",
                "dynamodb:DeleteItem",
                "dynamodb:GetItem",
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:UpdateItem"
            ],
            resources=[
                f"arn:aws:dynamodb:{self.region_id}:{self.account_id}:table/{self.DDBtableNewClaim}",
                f"arn:aws:dynamodb:{self.region_id}:{self.account_id}:table/{self.DDBtableFM}",
                f"arn:aws:dynamodb:{self.region_id}:{self.account_id}:table/{self.DDBtableVehiclePricing}",
                f"arn:aws:dynamodb:{self.region_id}:{self.account_id}:table/{self.DDBtableCustomerInfo}",
                f"arn:aws:dynamodb:{self.region_id}:{self.account_id}:table/{self.DDBtableCustomerInfo}",
                f"arn:aws:dynamodb:{self.region_id}:{self.account_id}:table/{self.DDBtableNewClaim}/index/*"
            ],
            effect=iam.Effect.ALLOW
        )
        
        
 
        # Define the gp-fsi-claimprocessing-docprocessor Lambda function
        docprocessor_lambda = lambda_.Function(
            self, "gp-fsi-claimprocessing-docprocessor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimprocessing-docprocessor",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimprocessing-docprocessor/"),  # Path to your Lambda code
            handler="gp-fsi-claimprocessing-docprocessor.lambda_handler",  # File name.function name
            environment= {
                "DDB_table_NewClaim": self.DDBtableNewClaim ,  # Replace if needed
                "DDB_table_VehiclePricing": self.DDBtableVehiclePricing  ,
                "DDB_table_FM": self.DDBtableFM
            },
        )
        
        docprocessor_lambda.role.add_to_principal_policy(self.s3bucket_policy_statement)
        docprocessor_lambda.role.add_to_principal_policy(self.dynamodb_policy_statement)
        docprocessor_lambda.role.add_to_principal_policy(self.bedrock_policy_statement)
        self.s3_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3n.LambdaDestination(docprocessor_lambda))
        # Attach the Textract AnalyzeID permission to the role
        docprocessor_lambda.role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["textract:AnalyzeID"],
                resources=["*"],
            )
        )
 
        # Define the gp-fsi-claimprocessing-BedrockAPICall Lambda function
        bedrockAPIcall_lambda = lambda_.Function(
            self, "gp-fsi-claimprocessing-bedrockAPIcall",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimprocessing-bedrockAPIcall",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimprocessing-bedrockAPIcall/"),  # Path to your Lambda code
            handler="gp-fsi-claimprocessing-bedrockAPIcall.lambda_handler",  # File name.function name
            environment= {
                "DDB_table_FM": self.DDBtableFM # Replace if needed
            },
        )
        
        bedrockAPIcall_lambda.role.add_to_principal_policy(self.dynamodb_policy_statement)
        bedrockAPIcall_lambda.role.add_to_principal_policy(self.bedrock_policy_statement)
        
        apigw_log_group = logs.LogGroup(self, "ApiGatewayClaimsLogs")
 
        # Create an API Gateway REST API
        self.api = apigateway.RestApi(self, "gp-fsi-claimprocessing-BedrockApi",
                rest_api_name="gp-fsi-claimprocessing-BedrockApi",
                cloud_watch_role=True,
                description="API Gateway for invoking Lambda function that calls bedrock gen AI",
                endpoint_types=[apigateway.EndpointType.REGIONAL],
                deploy_options=apigateway.StageOptions(
                    access_log_destination=apigateway.LogGroupLogDestination(apigw_log_group),
                    stage_name="dev"
                )
        )
        

       # Define the API Gateway resource and method
        api_resource = self.api.root.add_resource("lambda")
        api_method = api_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(bedrockAPIcall_lambda),
            api_key_required=False,
            method_responses=[
                apigateway.MethodResponse(status_code="200",
                response_models={"application/json": apigateway.Model.EMPTY_MODEL}
                )
            ]
        ) 
        
        # Deploy the API Gateway
        deployment = apigateway.Deployment(
            self, "Deployment",
            api=self.api,
            retain_deployments=True
        )
        
        
        # Grant the API Gateway permission to invoke the Lambda function
        self.API_gateway_arn=f"arn:aws:execute-api:{self.region_id}:{self.account_id}:{self.api.rest_api_id}/*/*/*"
        print(self.API_gateway_arn)
        #bedrockAPIcall_lambda.add_permission('PermitAPIGInvocation', principal=iam.ServicePrincipal("apigateway.amazonaws.com"), source_arn=self.API_gateway_arn)

        #Set up Auto inusrance Customer Login page and Simple Chat UI webpage
        
        local_asset_dir = os.path.join(os.getcwd(), "AmazonConnect/SampleConnectchatUI")
        
        #s3_deployment.BucketDeployment(
        #    self, "SampleConnectchatUI",
        #    sources=[s3_deployment.Source.asset(local_asset_dir)],
        #    destination_bucket=self.s3_bucket,
        #    destination_key_prefix="SampleConnectchatUI/"
        #    )
        
        s3_deployment.BucketDeployment(
            self,
            "SampleConnectchatUI",
            destination_bucket=self.s3_bucket,
            sources=[s3_deployment.Source.asset(os.path.join(os.getcwd(), "AmazonConnect/SampleConnectchatUI"))]
        )
            
        
           
        origin_access_identity = cloudfront.OriginAccessIdentity(self, "OriginAccessIdentity")
        self.s3_bucket.grant_read(origin_access_identity)

        '''
        # Create WAF WebACL
        web_acl1 = wafv2.CfnWebACL(
            self, "ChatBotWebpageWAF",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="CLOUDFRONT",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="ChatBotWebpageWAF",
                sampled_requests_enabled=True
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=1,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesCommonRuleSet",
                            vendor_name="AWS"
                        )
                    ),
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesCommonRuleSetMetric",
                        sampled_requests_enabled=True
                    )
                )
            ]
        )
        '''
        
        distribution = cloudfront.Distribution(
             self,
                "Distribution",
             comment="CloudFront distribution for Chat Webpage frontend application",
             default_root_object="index.html",
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(self.s3_bucket, origin_access_identity=origin_access_identity)
            ),
             #web_acl_id=web_acl1.attr_arn  # Associate the WAF WebACL with the CloudFront distribution
        )
    
        
        # Output the website URL
        CfnOutput(
            self, "WebsiteURL",
            value=f"https://{distribution.domain_name}",
            description="Website URL"
        )



        # Output the API Gateway endpoint URL
        cdk.CfnOutput(self,"API Gateway",value=self.api.url,description="API Gateway endpoint URL for Prod stage")
        
        #create bedrock knowledge base id

        
class ClaimsProcessingStack2(Stack):


    def __init__(self, scope: Construct, construct_id: str, ClaimsProcessingStack1, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
    
            
        '''Update the streamlit app'''
        path=os.getcwd()+"/claimsprocessing/"
        print(path)
        filenames=['GP-FSI-Claims-Processing-Initiate-Claim_org.py','GP-FSI-Claims-Processing-Upload-Documents_org.py','GP-FSI-Claims-Processing-XperienceCenter_org.py']
        for filename in filenames:
            filename=path+filename
            print(filename)
            print("Updating "+filename)
            # Read in the file
            with open(filename, 'r',encoding="utf-8") as file:
                filedata = file.read()
            
            print(ClaimsProcessingStack1.s3_bucket.bucket_name)
            print(ClaimsProcessingStack1.api.rest_api_id)
            # Replace the target string
            filedata = filedata.replace('replace_bucket_name',  ClaimsProcessingStack1.bucketname)
            filedata = filedata.replace('replace_account_id', ClaimsProcessingStack1.account_id)
            filedata = filedata.replace('replace_region_name', ClaimsProcessingStack1.region_id)
            filedata = filedata.replace('replace_Pinpoint_app_id', ClaimsProcessingStack1.Pinpoint_app_id)
            filedata = filedata.replace('replace_Pinpoint_origination_number', ClaimsProcessingStack1.Pinpoint_origination_number)
            filedata = filedata.replace('replace_DDBtableNewClaim', ClaimsProcessingStack1.DDBtableNewClaim)
            filedata = filedata.replace('replace_DDBtableCustomerInfo', ClaimsProcessingStack1.DDBtableCustomerInfo)
            filedata = filedata.replace('replace_DDBtableFM', ClaimsProcessingStack1.DDBtableFM)
            filedata = filedata.replace('replace_api_url', f"https://{ClaimsProcessingStack1.api.rest_api_id}.execute-api.{ClaimsProcessingStack1.region_id}.amazonaws.com/dev" )
            QueueUrl= f"https://sqs.{ClaimsProcessingStack1.region_id}.amazonaws.com/{ClaimsProcessingStack1.account_id}/GP-FSI-ClaimsProcessing-StatusNotification"
            filedata = filedata.replace('replace_QueueUrl',QueueUrl)
            
            if "Initiate" in filename:
                newfile=filename.replace("/claimsprocessing/","/claimsuidockerapp/demo_app/").replace("_org","")
            else:
                newfile=filename.replace("/claimsprocessing/","/claimsuidockerapp/demo_app/pages/").replace("_org","")
            
            print("new file path is ",newfile) 
            with open (newfile,"w",encoding="utf-8") as file:
                file.write(filedata)
            
        

class ClaimsProcessingStack3(Stack):


    def __init__(self, scope: Construct, construct_id: str, ClaimsProcessingStack1, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
                   
        # Get the current account ID and region from the CDK context
        print("printing value in stack 3 from stack 1")
        print("DDBtableNewClaim", ClaimsProcessingStack1.DDBtableNewClaim)
        print("DDBtableFM", ClaimsProcessingStack1.DDBtableFM)
        print("Pinpoint_origination_number", ClaimsProcessingStack1.Pinpoint_origination_number)
        
        """Streamlit UI stack for hosting Streamlit with ECS and Fargate"""
    
        platform_mapping = {
            "x86_64": ecs.CpuArchitecture.X86_64,
            "arm64": ecs.CpuArchitecture.ARM64
        }
        # Get architecture from platform (depending the machine that runs CDK)
        architecture = platform_mapping[platform.machine()] 

        # The code that defines your stack goes here
        # Build Docker image
        imageAsset = DockerImageAsset(self, "FrontendStreamlitImage",
            directory=("./claimsuidockerapp/")
        )

        # create app execute role
        app_execute_role = iam.Role(self, "AppExecuteRole",
                                    assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")                     
        )
        app_execute_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )  
        )
        
        app_execute_role.add_to_policy(ClaimsProcessingStack1.dynamodb_policy_statement)
        app_execute_role.add_to_policy(ClaimsProcessingStack1.pinpoint_policy_statement)
        app_execute_role.add_to_policy(ClaimsProcessingStack1.bedrock_policy_statement)
        app_execute_role.add_to_policy(ClaimsProcessingStack1.s3bucket_policy_statement)
        

        
        # create VPC to host the Ecs app
        vpc = ec2.Vpc(self, "StreamlitECSVpc", 
                      ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
                      subnet_configuration=[
                          ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC),
                          ec2.SubnetConfiguration(name="private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                          ec2.SubnetConfiguration(name="isolated", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
                      ]
        )
        ecs_cluster = ecs.Cluster(self, 'StreamlitAppCluster', 
                                  vpc=vpc)
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "StreamlitAppService",
                        cluster=ecs_cluster,
                        runtime_platform = ecs.RuntimePlatform(
                            operating_system_family=ecs.OperatingSystemFamily.LINUX,
                            cpu_architecture=architecture),
                        task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                            image=ecs.ContainerImage.from_docker_image_asset(imageAsset),
                            container_port=8501,
                            task_role=app_execute_role,
                        ), 
                        task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                        public_load_balancer=True,
                )

        # Configure health check for ALB
        fargate_service.target_group.configure_health_check(
            path="/healthz"
        )
        cdk.CfnOutput(
            self,
            'StreamlitLoadbalancer',
            value=fargate_service.load_balancer.load_balancer_dns_name)    
        
        # Custom header object
        custom_header_name = "X-Verify-Origin"
        custom_header_value = '-'.join((self.stack_name,"StreamLitCloudFrontDistribution"))
        '''
         # Create WAF WebACL
        web_acl2 = wafv2.CfnWebACL(
            self, "StreamlitWAF",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="CLOUDFRONT",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="StreamlitWAF",
                sampled_requests_enabled=True
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedRulesCommonRuleSet",
                    priority=1,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            name="AWSManagedRulesCommonRuleSet",
                            vendor_name="AWS"
                        )
                    ),
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSManagedRulesCommonRuleSetMetric",
                        sampled_requests_enabled=True
                    )
                )
            ]
        )
        '''
        # Create a CloudFront distribution
        cloudfront_distribution = cloudfront.Distribution(self, "StreamLitCloudFrontDistribution",
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.SSL_V3,
            comment="CloudFront distribution for Streamlit frontend application",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.LoadBalancerV2Origin(fargate_service.load_balancer, 
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY, 
                    http_port=80, 
                    origin_path="/", 
                    custom_headers = { custom_header_name : custom_header_value } ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_AND_CLOUDFRONT_2022,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS,
                compress=False
            ),
            #web_acl_id=web_acl2.attr_arn 
        )

        # Output the CloudFront distribution URL
        cdk.CfnOutput(self, "StreamlitURL", value=f"https://{cloudfront_distribution.domain_name}")
        

        
        # Create deny rule for ALB
        # Add a rule to deny traffic if custom header is absent
        elbv2.ApplicationListenerRule(self, "MyApplicationListenerRule",
            listener=fargate_service.listener,
            priority=1,
            conditions=[ elbv2.ListenerCondition.http_header( custom_header_name, [ custom_header_value ]) ],
            action = elbv2.ListenerAction.forward([fargate_service.target_group])
        )
        
        
        elbv2.ApplicationListenerRule(self, "RedirectApplicationListenerRule",
            listener=fargate_service.listener,
            priority=5,
            conditions=[ elbv2.ListenerCondition.path_patterns(["*"]) ],
            action = elbv2.ListenerAction.redirect(host=cloudfront_distribution.domain_name, permanent=True,protocol="HTTPS",port="443")
        )
        
        
        #customernotification_lambda = lambda_.Function.from_function_arn(
        #    self, "ExistingLambda",
        #    function_arn=ClaimsProcessingStack1.customernotification_lambda.function_arn
        #)
        # Update the environment variable
        #customernotification_lambda.add_environment("CloudFront_URL", f"https://{cloudfront_distribution.domain_name}")
        
        # Create an SQS queue
        StatusNotification_queue = sqs.Queue(
            self, "MyQueue",
            queue_name="GP-FSI-ClaimsProcessing-StatusNotification",
            visibility_timeout=Duration.seconds(1200)  # Set visibility timeout to 20 minutes
        )
 
 
        app_execute_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "sqs:SendMessage",
                "sqs:GetQueueAttributes",
                "sqs:GetQueueUrl"
            ],
            resources=[StatusNotification_queue.queue_arn]
        ))
        
        
         #Lambad using the Cloudfront uRL
        # Define the  gp-fsi-claimprocessing-customernotification Lambda function
        customernotification_lambda = lambda_.Function(
            self, "gp-fsi-claimprocessing-notification",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimprocessing-notification",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimprocessing-customernotification/"),  # Path to your Lambda code
            handler="gp-fsi-claimprocessing-customernotification.lambda_handler",  # File name.function name
            environment= {
                "DDB_table_NewClaim": ClaimsProcessingStack1.DDBtableNewClaim,  # Replace if needed
                "Pinpoint_app_id": ClaimsProcessingStack1.Pinpoint_app_id,
                "Pinpoint_origination_number": ClaimsProcessingStack1.Pinpoint_origination_number,
                "CloudFront_URL":f"https://{cloudfront_distribution.domain_name}"
            },
        )
        customernotification_lambda.role.add_to_principal_policy(ClaimsProcessingStack1.pinpoint_policy_statement)
        customernotification_lambda.role.add_to_principal_policy(ClaimsProcessingStack1.dynamodb_policy_statement)
        #StatusNotification_queue.grant_consume_messages(ClaimsProcessingStack1.customernotification_lambda)
        
        # Create an event source mapping between the SQS queue and the Lambda function
        customernotification_lambda.add_event_source(lambda_event_sources.SqsEventSource(StatusNotification_queue))
        
        
        # Define the  gp-fsi-claimprocessing-filenewclaim Lambda function
        filenewclaim_lambda = lambda_.Function(
            self, "gp-fsi-claimprocessing-filenewclaim",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimprocessing-filenewclaim",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimprocessing-filenewclaim/"),  # Path to your Lambda code
            handler="gp-fsi-claimprocessing-filenewclaim.lambda_handler",  # File name.function name
            environment= {
                "DDB_table_NewClaim": ClaimsProcessingStack1.DDBtableNewClaim,  # Replace if needed
                "DDB_table_CustomerInfo": ClaimsProcessingStack1.DDBtableCustomerInfo,  
                "Pinpoint_app_id": ClaimsProcessingStack1.Pinpoint_app_id,
                "Pinpoint_origination_number": ClaimsProcessingStack1.Pinpoint_origination_number,
                "CloudFront_URL":f"https://{cloudfront_distribution.domain_name}"
            },
        )
      
        
        # You can grant specific permissions using IAM statements
        filenewclaim_lambda.role.add_to_principal_policy(ClaimsProcessingStack1.pinpoint_policy_statement)
        filenewclaim_lambda.role.add_to_principal_policy(ClaimsProcessingStack1.dynamodb_policy_statement)
        
        lex_principal = iam.ServicePrincipal("lex.amazonaws.com")
        
        filenewclaim_lambda.grant_invoke(lex_principal)

        filenewclaim_lambda.add_permission(
            "AllowLexToInvokeLambda",
            principal=lex_principal,
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:lex:{ClaimsProcessingStack1.region}:{ClaimsProcessingStack1.account}:bot:GP-FSI-Claims-Processing:*"
        )
      
        
        
class ClaimsProcessingStack4(Stack):

    def __init__(self, scope: Construct, construct_id: str, ClaimsProcessingStack1, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)    
        # Create a custom role for Lex
        
        self.lex_role_name="gp-fsi-claims-processing-lex-role"
        
        lex_role = iam.Role(
            self, "LexCustomRole",
            role_name=self.lex_role_name,
            assumed_by=iam.ServicePrincipal("lex.amazonaws.com"),
            description="Custom role for Amazon Lex with CloudWatch and Polly permissions"
        )

        # Add Lex permissions
        #lex_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonLexFullAccess"))

        # Add CloudWatch permissions
        lex_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            resources=[ f"arn:aws:logs:{ClaimsProcessingStack1.region_id}:{ClaimsProcessingStack1.account_id}:log-group:{self.lex_role_name}:*"]
        ))
        
        
        lex_role.add_to_policy(ClaimsProcessingStack1.bedrock_policy_statement)
        
        # Add Polly permissions
        lex_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "polly:SynthesizeSpeech"
            ],
            resources=["*"]
        ))

        # Output the ARN of the created role
        self.lex_role_arn = lex_role.role_arn
        
        os.environ['lex_role_arn'] = self.lex_role_arn
        
        CfnOutput(self, "LexRoleArn",
            value=self.lex_role_arn,
            description="The ARN of the Lex custom role"
        )
         