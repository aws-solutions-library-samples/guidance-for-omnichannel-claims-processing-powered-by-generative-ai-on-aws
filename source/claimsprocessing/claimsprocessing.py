from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3_deployment,
    aws_s3 as s3,
    aws_sqs as sqs,
    aws_logs as logs,
    aws_lambda as lambda_,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_lambda_event_sources as lambda_event_sources,
    aws_apigateway as apigateway,
    CfnOutput,
    aws_s3_notifications as s3n,
    aws_wafv2 as wafv2,
    aws_cognito as cognito,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    CustomResource,
    custom_resources as cr
)
from cdklabs.generative_ai_cdk_constructs import bedrock

import os

class ClaimsProcessingStack1(Stack):


    def __init__(self, scope: Construct, construct_id: str, stack_variables: str = None,**kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.template_options.description = "Guidance for Omnichannel Claims Processing Powered by Generative AI on AWS(SO9552)"


                   
        # Get the current account ID and region from the CDK context
        self.account_id = Stack.of(self).account
        self.region_id = Stack.of(self).region
        
        # Get account ID

        # Create bucket name with fallback
        base_bucket_name = stack_variables.get('bucketname_input')
        if not base_bucket_name:
            raise ValueError("bucketname_input is required in stack_variables")
        
        self.bucketname = f"{base_bucket_name}-{self.account_id}"

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
        self.SMS_Origination_number_ARN=stack_variables['SMS_Origination_number_ARN']
        #print("SMS_Origination_number_ARN", self.SMS_Origination_number_ARN)
        # Prefix for naming conventions
        prefix = "gp-fsi-claims-processing"
        self.reactpath=stack_variables['reactpath']

        self.SOCOTRA_ENDPOINT=stack_variables['SOCOTRA_ENDPOINT']
        self.SOCOTRA_HOST=stack_variables['SOCOTRA_HOST']
        self.SOCOTRA_USERNAME=stack_variables['SOCOTRA_USERNAME']
        self.SOCOTRA_PASSWORD=stack_variables['SOCOTRA_PASSWORD']

        self.GW_USERNAME=stack_variables['GW_USERNAME']
        self.GW_PASSWORD=stack_variables['GW_PASSWORD']
        self.GW_BASE_URL=stack_variables['GW_BASE_URL']


        self.execution=stack_variables['execution']  
        
        """Generic permissions"""
        
        # Define the Bedrock policy statement
        self.bedrock_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:InvokeModel","bedrock:ListFoundationModels","bedrock:Retrieve","bedrock:RetrieveAndGenerate"],
            resources=[
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-v2:1",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-v2",
                "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
                "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v1",
                "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0",
                #"arn:aws:bedrock:*:*:knowledge-base/"+BedrockKBID,  
                "arn:aws:bedrock:*:*:knowledge-base/*" #If you have a Knowledge base, you can comment out this line and provide the ID in the above line
            ]
        )

        
        # self.pinpoint_policy_statement = iam.PolicyStatement(
        #         actions=[
        #             "mobiletargeting:GetSmsChannel",
        #             "mobiletargeting:SendMessages",
        #             "mobiletargeting:PhoneNumberValidate"
        #         ],
        #         resources=[f"arn:aws:mobiletargeting:{self.region_id}:{self.account_id}:*"],
        #         effect=iam.Effect.ALLOW
        #     )
        
        # Update the SMS policy statement in your claimsprocessing.py
        self.sms_policy_statement = iam.PolicyStatement(
            actions=[
                    "sms-voice:SendTextMessage",
                    "pinpoint-sms-voice-v2:SendTextMessage",  # Add this new permission
                    "pinpoint:SendMessages",
                    "mobiletargeting:SendMessages"
            ],
            resources=["*"],  # Using * to ensure full access.. you can limit the access to specific resources
            effect=iam.Effect.ALLOW
        )

        """Generic Resources"""

        cf_logs_bucket = s3.Bucket(self, "gp-claims-processing-log",
            bucket_name=f"gp-claims-processing-log-{self.account_id }",  # Optional: provide a custom name
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_PREFERRED,  # Enable ACLs
            access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE  # Allow CloudFront to write logs
        )



        # Create Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, 'ClaimsProcessingUserPool-test',
            user_pool_name='claims-processing-user-pool-test',
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True
            ),
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                )
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY
        )

        
        # Create User Pool Client
        self.user_pool_client = self.user_pool.add_client(
            'ClaimsProcessingUserPoolClient-test',
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[cognito.OAuthScope.EMAIL, 
                        cognito.OAuthScope.OPENID, 
                        cognito.OAuthScope.PROFILE],
                callback_urls=['https://{self.distribution.distribution_domain_name}'],  # Update with your callback URLs
                logout_urls=['https://{self.distribution.distribution_domain_name}']     # Update with your logout URLs
            ),
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True
            ),
            prevent_user_existence_errors=True
        )

        # Create Cognito Identity Pool
        self.identity_pool = cognito.CfnIdentityPool(
            self, 'gp-ClaimsProcessingIdentityPool',
            identity_pool_name='gp-ClaimsProcessingIdentityPool',
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name,
                    server_side_token_check=True
                )
            ]
        )

        # Create roles for authenticated and unauthenticated users
        authenticated_role = iam.Role(
            self, 'gp-ClaimsProcessing-CognitoAuthenticatedRole',
            assumed_by=iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com',
                conditions={
                    'StringEquals': {
                        'cognito-identity.amazonaws.com:aud': self.identity_pool.ref
                    },
                    'ForAnyValue:StringLike': {
                        'cognito-identity.amazonaws.com:amr': 'authenticated'
                    }
                },
                assume_role_action='sts:AssumeRoleWithWebIdentity'
            )
        )

        # Optionally, you might also want to add other permissions

        # Attach roles to Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(
            self, 'gp-ClaimsProcessing-IdentityPoolRoleAttachment',
            identity_pool_id=self.identity_pool.ref,
            roles={
                'authenticated': authenticated_role.role_arn
            }
        )

        # Create User Pool Domain
        self.user_pool_domain = self.user_pool.add_domain(
            'gp-ClaimsProcessing-ClaimsProcessingDomaing',
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f'gp-claimsprocessing-domain-{self.account_id}'  # Must be unique across AWS
            )
        )

        
        allowed_origins = [
            'http://localhost:3000',
            'https://d1k95x9rijj02c.cloudfront.net'  # Add your production domain
        ]
        # Create S3 bucket 
        self.s3_bucket = s3.Bucket(
            self, 'GP-FSI-ClaimsProcessing',
            bucket_name=self.bucketname,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY, 
            auto_delete_objects=True, 
            enforce_ssl=True,
            cors=[
            s3.CorsRule(
            allowed_methods=[
                s3.HttpMethods.PUT,
                s3.HttpMethods.POST,
                s3.HttpMethods.DELETE,
                s3.HttpMethods.GET,
                s3.HttpMethods.HEAD,
            ],
            allowed_origins=allowed_origins,
            allowed_headers=[
                '*',
            ],
            exposed_headers=[
                'ETag'
            ],
            max_age=3000
        )
        ],
        )
        
        self.s3bucket_policy_statement = iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject",  "s3:DeleteObject","s3:ListBucket"],
                resources=[self.s3_bucket.bucket_arn, f"{self.s3_bucket.bucket_arn}/*"]
        )  
        

    
        # Create CloudFront cache policy
        cache_policy = cloudfront.CachePolicy(self, 'CachePolicy',
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Authorization"),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_brotli=True,
            enable_accept_encoding_gzip=True,
            min_ttl=Duration.seconds(1),
            max_ttl=Duration.seconds(10),
            default_ttl=Duration.seconds(5)
        )

        # Create WAF Web ACL
        claims_processing_web_acl = wafv2.CfnWebACL(self, "gp_claims_processing_web_acl",
            name="claims_processing_web_acl",  # Add a name property
            default_action={"allow": {}},
            scope="CLOUDFRONT",
            visibility_config={
                "cloudWatchMetricsEnabled": True,
                "metricName": "gp_claims_processing_metric",
                "sampledRequestsEnabled": True
            },
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesCommonRuleSet",
                    priority=0,
                    override_action={"none": {}},
                    statement={
                        "managedRuleGroupStatement": {
                            "vendorName": "AWS",
                            "name": "AWSManagedRulesCommonRuleSet"
                        }
                    },
                    visibility_config={
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": True,
                        "metricName": "AWS-AWSManagedRulesCommonRuleSet"
                    }
                ),
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesKnownBadInputsRuleSet",
                    priority=1,
                    override_action={"none": {}},
                    statement={
                        "managedRuleGroupStatement": {
                            "vendorName": "AWS",
                            "name": "AWSManagedRulesKnownBadInputsRuleSet"
                        }
                    },
                    visibility_config={
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": True,
                        "metricName": "AWS-AWSManagedRulesKnownBadInputsRuleSet"
                    }
                ),
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesAmazonIpReputationList",
                    priority=2,
                    override_action={"none": {}},
                    statement={
                        "managedRuleGroupStatement": {
                            "vendorName": "AWS",
                            "name": "AWSManagedRulesAmazonIpReputationList"
                        }
                    },
                    visibility_config={
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": True,
                        "metricName": "AWS-AWSManagedRulesAmazonIpReputationList"
                    }
                )
            ]
        )



        
     # Create CloudFront Origin Access Identity
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "OAI",
            comment="OAI for React App"
        )

        # Create CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, "ReactAppDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.s3_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html"
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"
                )
            ]
        )
            
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
        self.s3_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3n.LambdaDestination(docprocessor_lambda),s3.NotificationKeyFilter(prefix="upload/"))
        # Attach the Textract AnalyzeID permission to the role
        docprocessor_lambda.role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=["textract:AnalyzeID"],
                resources=["*"],
            )
        )


        # Create an SQS queue for Notification
        StatusNotification_queue = sqs.Queue(
            self, "StatusNotification Queue",
            queue_name="GP-FSI-ClaimsProcessing-StatusNotification",
            visibility_timeout=Duration.seconds(1200)  # Set visibility timeout to 20 minutes
        )

        # Define the  gp-fsi-claimprocessing-customernotification Lambda function
        customernotification_lambda = lambda_.Function(
            self, "gp-fsi-claimprocessing-notification",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimprocessing-notification",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimprocessing-customernotification/"),  # Path to your Lambda code
            handler="gp-fsi-claimprocessing-customernotification.lambda_handler",  # File name.function name
            environment= {
                "DDBtableCustomerInfo": self.DDBtableCustomerInfo,  # Replace if needed
                "SMS_Origination_number_ARN": self.SMS_Origination_number_ARN,
                "CloudFront_URL":f"https://{self.distribution.distribution_domain_name}"
            },
        )
        customernotification_lambda.role.add_to_principal_policy(self.sms_policy_statement)
        customernotification_lambda.role.add_to_principal_policy(self.dynamodb_policy_statement)
        #StatusNotification_queue.grant_consume_messages(self.customernotification_lambda)
        
        # Create an event source mapping between the SQS queue and the Lambda function
        customernotification_lambda.add_event_source(lambda_event_sources.SqsEventSource(StatusNotification_queue))



        # Create an SQS queue for 3P Integration
        Integration_3P_queue = sqs.Queue(
            self, "Queue for 3P integration",
            queue_name="GP-FSI-ClaimsProcessing-3PIntegration",
            visibility_timeout=Duration.seconds(1200)  # Set visibility timeout to 20 minutes
        )
    
        # Below VPC and networking setting is for AWS Lambda to be deployed in a VPC and access the Guidewire using the allowed IP listing 
        # 1. Create a new VPC
        vpc = ec2.Vpc(
            self, 
            "GPClaimsProcessing",
            vpc_name="GPClaimsProcessing",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            # Create an empty VPC without any default configuration
            nat_gateways=0,
            subnet_configuration=[],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )

        # 2. Create and attach Internet Gateway
        igw = ec2.CfnInternetGateway(
            self, 
            "CustomIGW",
            tags=[{"key": "Name", "value": "CustomIGW"}]
        )

        vpc_igw_attachment = ec2.CfnVPCGatewayAttachment(
            self,
            "CustomIGWAttachment",
            vpc_id=vpc.vpc_id,
            internet_gateway_id=igw.ref
        )

        # 3. Create Public Subnet
        public_subnet = ec2.Subnet(
            self,
            "PublicSubnet",
            vpc_id=vpc.vpc_id,
            availability_zone=f"{self.region}a",
            cidr_block="10.0.1.0/24",
            map_public_ip_on_launch=True
        )

        # Create and configure public route table
        public_route_table = ec2.CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=vpc.vpc_id,
            tags=[{"key": "Name", "value": "PublicRouteTable"}]
        )

        # Associate public subnet with public route table
        ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnetRouteTableAssociation",
            route_table_id=public_route_table.ref,
            subnet_id=public_subnet.subnet_id
        )

        # Add route to Internet Gateway
        publicroute=ec2.CfnRoute(
            self,
            "PublicRoute",
            route_table_id=public_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=igw.ref
        )

        publicroute.add_dependency(vpc_igw_attachment)

        # 4. Create Elastic IP
        eip = ec2.CfnEIP(
            self,
            "NatGatewayEIP",
            domain="vpc"
        )

        # 6. Create Private Subnet
        private_subnet = ec2.Subnet(
            self,
            "PrivateSubnet",
            vpc_id=vpc.vpc_id,
            availability_zone=f"{self.region}a",
            cidr_block="10.0.2.0/24",
            map_public_ip_on_launch=False
        )


       # Create Security Group for Lambda with all necessary rules
        lambda_security_group = ec2.SecurityGroup(
            self,
            "LambdaSecurityGroup",
            vpc=vpc,
            description="Security group for Lambda function",
            allow_all_outbound=True  # Initially allow all outbound
        )

        # Add explicit outbound rules for HTTPS and DNS
        lambda_security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),  # HTTPS
            description="Allow HTTPS outbound traffic"
        )

        lambda_security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),  # HTTP
            description="Allow HTTP outbound traffic"
        )

        # Add DNS rules
        lambda_security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(53),  # DNS over TCP
            description="Allow DNS (TCP) outbound traffic"
        )

        lambda_security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.udp(53),  # DNS over UDP
            description="Allow DNS (UDP) outbound traffic"
        )

        # Create NAT Gateway with proper dependencies
        nat_gateway = ec2.CfnNatGateway(
            self,
            "NatGateway",
            subnet_id=public_subnet.subnet_id,
            allocation_id=eip.attr_allocation_id,
            tags=[{"key": "Name", "value": "CustomNATGateway"}]
        )

        # Add explicit dependency on IGW attachment
        nat_gateway.add_dependency(vpc_igw_attachment)

        # Create private route table with NAT Gateway route
        private_route_table = ec2.CfnRouteTable(
            self,
            "PrivateRouteTable",
            vpc_id=vpc.vpc_id,
            tags=[{"key": "Name", "value": "PrivateRouteTable"}]
        )

        # Add route to NAT Gateway with explicit dependency
        private_route = ec2.CfnRoute(
            self,
            "PrivateRoute",
            route_table_id=private_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=nat_gateway.ref
        )
        private_route.add_dependency(nat_gateway)

        # Associate private subnet with private route table
        private_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            self,
            "PrivateSubnetRouteTableAssociation",
            route_table_id=private_route_table.ref,
            subnet_id=private_subnet.subnet_id
        )
        private_route_table_assoc.add_dependency(private_route)

        
        # Define the  SQS_3P_integration_lambda  Lambda function
        SQS_3P_integration_lambda = lambda_.Function(
            self, "gp-fsi-claimsprocessing-SQS-3P-integration",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimsprocessing-SQS-3P-integration",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimsprocessing-SQS-3P-integration/"),  # Path to your Lambda code
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[private_subnet]),
            security_groups=[lambda_security_group],
            handler="gp-fsi-claimsprocessing-SQS-3P-integration.lambda_handler",  # File name.function name
            environment= {
                "SOCOTRA_ENDPOINT":self.SOCOTRA_ENDPOINT,
                "SOCOTRA_HOST":self.SOCOTRA_HOST,
                "SOCOTRA_USERNAME":self.SOCOTRA_USERNAME,
                "SOCOTRA_PASSWORD":self.SOCOTRA_PASSWORD,
                "GW_USERNAME":self.GW_USERNAME,
                "GW_PASSWORD":self.GW_PASSWORD,
                "GW_BASE_URL":self.GW_BASE_URL,
            }
        )

        SQS_3P_integration_lambda.role.add_to_principal_policy(self.dynamodb_policy_statement)
        # Create an event source mapping between the SQS queue and the Lambda function
        SQS_3P_integration_lambda.add_event_source(lambda_event_sources.SqsEventSource(Integration_3P_queue))


        # Add necessary permissions for the Lambda function
        SQS_3P_integration_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface"
                ],
                resources=["*"]
            )
        )

        # Define the  gp-fsi-claimprocessing-filenewclaim Lambda function
        filenewclaim_lambda = lambda_.Function(
            self, "gp-fsi-claimprocessing-filenewclaim",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimprocessing-filenewclaim",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimprocessing-filenewclaim/"),  # Path to your Lambda code
            handler="gp-fsi-claimprocessing-filenewclaim.lambda_handler",  # File name.function name
            environment= {
                "DDB_table_NewClaim": self.DDBtableNewClaim,  # Replace if needed
                "DDB_table_CustomerInfo": self.DDBtableCustomerInfo,  
                "SMS_Origination_number_ARN": self.SMS_Origination_number_ARN,
                "CloudFront_URL":f"https://{self.distribution.distribution_domain_name}",
                "SQS_3P_QUEUE_URL":Integration_3P_queue.queue_url,
                "CUSTOMER_SQS_QUEUE_URL":StatusNotification_queue.queue_url,
            },
        )
      
        
        # You can grant specific permissions using IAM statements
        filenewclaim_lambda.role.add_to_principal_policy(self.sms_policy_statement)
        filenewclaim_lambda.role.add_to_principal_policy(self.dynamodb_policy_statement)
    

        filenewclaim_lambda.role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sqs:SendMessage"],
            resources=[ Integration_3P_queue.queue_arn,
                       StatusNotification_queue.queue_arn
                ]
        )
        )
        
        lex_principal = iam.ServicePrincipal("lex.amazonaws.com")
        
        filenewclaim_lambda.grant_invoke(lex_principal)

        filenewclaim_lambda.add_permission(
            "AllowLexToInvokeLambda",
            principal=lex_principal,
            action="lambda:InvokeFunction",
            source_arn=f"arn:aws:lex:{self.region}:{self.account}:bot:GP-FSI-Claims-Processing:*"
        )
        
        self.lex_role_name="gp-fsi-claims-processing-lex-role"
        
        # Create the IAM role for Lex
        lex_role = iam.Role(
            self, "gp-fsi-claims-processing-lex-role",
            role_name=self.lex_role_name,
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lex.amazonaws.com"),
                iam.ServicePrincipal("connect.amazonaws.com")
            ),
            description="Custom role for Amazon Lex with CloudWatch and Polly permissions"
        )

        # Add CloudWatch permissions
        lex_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams"
            ],
            resources=[f"arn:aws:logs:{self.region_id}:{self.account_id}:log-group:{self.lex_role_name}:*"]
        ))

        # Add Polly permissions
        lex_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "polly:SynthesizeSpeech"
            ],
            resources=["*"]
        ))

        # Add Lex permissions
        lex_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "lex:RecognizeText",
                "lex:StartConversation",
                "lex:RecognizeUtterance",
                "lex:PutSession",
                "lex:GetSession",
                "lex:DeleteSession"
            ],
            resources=[f"arn:aws:lex:{self.region_id}:{self.account_id}:bot-alias/*"]
        ))

        # Add Bedrock permissions (if you had them before)
        lex_role.add_to_policy(self.bedrock_policy_statement)


        # Output the ARN of the created role
        self.lex_role_arn = lex_role.role_arn
        
        os.environ['lex_role_arn'] = self.lex_role_arn


        authenticated_role.add_to_principal_policy(self.s3bucket_policy_statement)
        authenticated_role.add_to_principal_policy(self.dynamodb_policy_statement)



        apigw_log_group = logs.LogGroup(self, "ApiGatewayClaimsLogs")

        # Define the gp-fsi-claimprocessing-BedrockAPICall Lambda function
        bedrockAPIcall_lambda = lambda_.Function(
            self, "gp-fsi-claimprocessing-bedrockAPIcall",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimprocessing-bedrockAPIcall",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimprocessing-bedrockAPIcall/"),  # Path to your Lambda code
            handler="gp-fsi-claimprocessing-bedrockAPIcall.lambda_handler",  # File name.function name
            environment= {
                "DDB_table_FM": self.DDBtableFM
            },
        )
        bedrockAPIcall_lambda.role.add_to_principal_policy(self.dynamodb_policy_statement)
        bedrockAPIcall_lambda.role.add_to_principal_policy(self.bedrock_policy_statement)


        # Create an API Gateway REST API
        self.rest_api = apigateway.RestApi(self, "gp-fsi-claimprocessing-BedrockApi",
                rest_api_name="gp-fsi-claimprocessing-BedrockApi",
                cloud_watch_role=True,
                description="API Gateway for invoking Lambda function that calls bedrock gen AI",
                endpoint_types=[apigateway.EndpointType.REGIONAL],
                deploy_options=apigateway.StageOptions(
                    access_log_destination=apigateway.LogGroupLogDestination(apigw_log_group),
                    stage_name="dev"
                ),
        )
        

        # Create POST method integration
        post_integration = apigateway.LambdaIntegration(
            bedrockAPIcall_lambda,
            proxy=False,
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    },
                    response_templates={
                        'application/json': ''  # Passthrough
                    }
                ),
                apigateway.IntegrationResponse(
                    status_code="500",
                    selection_pattern="(\n|.)+",  # Catch all errors
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    },
                    response_templates={
                        'application/json': '{"message": $input.json(\'$.errorMessage\')}'
                    }
                )
            ],
            passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
        )
        
        # Add POST method to the root resource
        self.rest_api.root.add_method(
            "POST",
            post_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    },
                    response_models={
                        'application/json': apigateway.Model.EMPTY_MODEL
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    },
                    response_models={
                        'application/json': apigateway.Model.ERROR_MODEL
                    }
                )
            ]
        )

        # Add OPTIONS method for CORS
        options_integration = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'OPTIONS,POST'"
                    }
                )
            ],
            passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
            request_templates={
                "application/json": '{"statusCode": 200}'
            }
        )

        self.rest_api.root.add_method(
            "OPTIONS",
            options_integration,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Headers': True,
                        'method.response.header.Access-Control-Allow-Methods': True,
                        'method.response.header.Access-Control-Allow-Origin': True
                    },
                    response_models={
                        'application/json': apigateway.Model.EMPTY_MODEL
                    }
                )
            ]
        )


        # Add deployment and stage (optional if you want to specify stage settings)
        deployment = apigateway.Deployment(
            self, 
            "React App Bedrock API Deployment",
            api=self.rest_api
        )

        # Deploy documents to S3
        s3_deployment.BucketDeployment(
            self, 'gp_claimsprocessingDocsUpload',
            sources=[s3_deployment.Source.asset("Knowledgebase/")],
            destination_bucket=self.s3_bucket
        )

        # Now you can safely reference the s3_bucket and distribution
        s3_deployment.BucketDeployment(
            self, "DeployReactApp",
            sources=[s3_deployment.Source.asset("ReactApp/build")],
            destination_bucket=self.s3_bucket,
            distribution=self.distribution,
            distribution_paths=["/*"]
        )


        # Define the gp-fsi-claimsprocessing-3P-integration Lambda function
        claimsprocessing_3P_integration_lambda = lambda_.Function(
            self, "gp-fsi-claimsprocessing-3P-integration",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(900),
            function_name="gp-fsi-claimsprocessing-3P-integration",
            code=lambda_.Code.from_asset("lambda/gp-fsi-claimsprocessing-3P-integration/"),  # Path to your Lambda code
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[private_subnet]),
            security_groups=[lambda_security_group],
            handler="gp-fsi-claimsprocessing-3P-integration.lambda_handler",
            environment= {
                "SOCOTRA_ENDPOINT":self.SOCOTRA_ENDPOINT,
                "SOCOTRA_HOST":self.SOCOTRA_HOST,
                "SOCOTRA_USERNAME":self.SOCOTRA_USERNAME,
                "SOCOTRA_PASSWORD":self.SOCOTRA_PASSWORD,
                "GW_USERNAME":self.GW_USERNAME,
                "GW_PASSWORD":self.GW_PASSWORD,
                "GW_BASE_URL":self.GW_BASE_URL,
            },
        )
        #claimsprocessing_3P_integration_lambda.role.add_to_principal_policy(self.dynamodb_policy_statement)
        #claimsprocessing_3P_integration_lambda.role.add_to_principal_policy(self.bedrock_policy_statement)



        # Create an API Gateway REST API
        self.api_3p_Integration = apigateway.RestApi(self, "gp-fsi-claimsprocessing-3P-integration-API",
                rest_api_name="gp-fsi-claimsprocessing-3P-integration-API",
                cloud_watch_role=True,
                description="API Gateway for invoking Lambda function that calls 3P Claims systems",
                endpoint_types=[apigateway.EndpointType.REGIONAL],
                deploy_options=apigateway.StageOptions(
                    access_log_destination=apigateway.LogGroupLogDestination(apigw_log_group),
                    stage_name="dev"),
        )
        

        # Create POST method integration
        post_integration_3P = apigateway.LambdaIntegration(
            claimsprocessing_3P_integration_lambda,
            proxy=False,
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    },
                    response_templates={
                        'application/json': ''  # Passthrough
                    }
                ),
                apigateway.IntegrationResponse(
                    status_code="500",
                    selection_pattern="(\n|.)+",  # Catch all errors
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    },
                    response_templates={
                        'application/json': '{"message": $input.json(\'$.errorMessage\')}'
                    }
                )
            ],
            passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
        )
        
        # Add POST method to the root resource
        self.api_3p_Integration.root.add_method(
            "POST",
            post_integration_3P,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    },
                    response_models={
                        'application/json': apigateway.Model.EMPTY_MODEL
                    }
                ),
                apigateway.MethodResponse(
                    status_code="500",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    },
                    response_models={
                        'application/json': apigateway.Model.ERROR_MODEL
                    }
                )
            ]
        )

        # Add OPTIONS method for CORS
        options_integration_3p = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'OPTIONS,POST'"
                    }
                )
            ],
            passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
            request_templates={
                "application/json": '{"statusCode": 200}'
            }
        )

        self.api_3p_Integration.root.add_method(
            "OPTIONS",
            options_integration_3p,
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Headers': True,
                        'method.response.header.Access-Control-Allow-Methods': True,
                        'method.response.header.Access-Control-Allow-Origin': True
                    },
                    response_models={
                        'application/json': apigateway.Model.EMPTY_MODEL
                    }
                )
            ]
        )


        # Add deployment and stage (optional if you want to specify stage settings)
        deployment = apigateway.Deployment(
            self, 
            "React App 3P API Deployment",
            api=self.api_3p_Integration
        )


        authenticated_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["sqs:SendMessage"],
            resources=[ Integration_3P_queue.queue_arn,
                       StatusNotification_queue.queue_arn
                      ]
        ))

        ssm_params = {
            'AWS_REGION': self.region,
            'AWS_ACCOUNT_ID': self.account,
            'DDBTableNameClaim': 'GP-FSI-ClaimsProcessing-NewClaim',
            'DDBTableNameCustomer': 'GP-FSI-ClaimsProcessing-CustomerInfo',
            'REACT_APP_DDBTableNameFM':'GP-FSI-ClaimsProcessing-FM',
            'COGNITO_USER_POOL_ID': self.user_pool.user_pool_id,
            'COGNITO_CLIENT_ID': self.user_pool_client.user_pool_client_id,
            'REACT_APP_IDENTITY_POOL_ID': self.identity_pool.ref,
            'REACT_APP_S3BUCKET': self.bucketname,
            'REACT_APP_NOTIFICATION_SQS_QUEUE_URL': f"https://sqs.{self.region_id}.amazonaws.com/{self.account_id}/GP-FSI-ClaimsProcessing-StatusNotification" ,
            'REACT_APP_3P_SQS_QUEUE_URL': f"https://sqs.{self.region_id}.amazonaws.com/{self.account_id}/GP-FSI-ClaimsProcessing-3PIntegration",
            'REACT_APP_3PAPI': self.api_3p_Integration.url,
            'REACT_APP_REACTAPI':self.rest_api.url,
            'REACT_APP_CLOUDFRONT_URL': self.distribution.distribution_domain_name,
            'CLOUDFRONT_DISTRIBUTION_ID': self.distribution.distribution_id
        }

        # Create SSM parameters
        self.ssm_parameters = {}
        for key, value in ssm_params.items():
            parameter = ssm.StringParameter(
                self, f'{key}',
                parameter_name=f'/GP-FSI-ClaimsProcessing/{key}',
                string_value=value,
                description=f'{key} for  GP-FSI-ClaimsProcessing',
                tier=ssm.ParameterTier.STANDARD,
                # For sensitive data, use:
                # tier=ssm.ParameterTier.SECURE_STRING,
            )
            self.ssm_parameters[key] = parameter

        #set up Bedrock knowledgebase:

        kb = bedrock.VectorKnowledgeBase(self, 'KnowledgeBase',
                    name="gp-fsi-claims-processing-knowledgebase",
                    embeddings_model= bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V1,
                    instruction=  'Use this knowledge base to answer questions about insurance relared questions as part of the Claims Processing GP'
                )
    
        
        bedrock.S3DataSource(self, 'DataSource',
            bucket= self.s3_bucket,
            knowledge_base=kb,
            inclusion_prefixes=["Knowledgebase/"],
            data_source_name='gp-fsi-claims-processing-knowledgebase',
            chunking_strategy= bedrock.ChunkingStrategy.FIXED_SIZE,
        )


       
        #Output BucketName
        CfnOutput(
            self, "S3bucketName",
            value=self.s3_bucket.bucket_name,
            description="S3bucketName"
        )

        # Output the CloudFront URL
        CfnOutput(
            self, "CloudFrontURL",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="URL of the CloudFront distribution"
        )


        CfnOutput(
            self, 'UserPoolId',
            value=self.user_pool.user_pool_id,
            description='Cognito User Pool ID'
        )

        CfnOutput(
            self, 'UserPoolClientId',
            value=self.user_pool_client.user_pool_client_id,
            description='Cognito User Pool Client ID'
        )

        CfnOutput(
            self, 'IdentityPoolId',
            value=self.identity_pool.ref,
            description='Cognito Identity Pool ID'
        )

        CfnOutput(
            self, 'UserPoolDomainUrl',
            value=self.user_pool_domain.domain_name,
            description='Cognito User Pool Domain URL'
        )

                
        CfnOutput(self, "LexRoleArn",
            value=self.lex_role_arn,
            description="The ARN of the Lex custom role"
        )

        # Output the API URL
        CfnOutput(
            self, 'React App Bedrock API',
            value=self.rest_api.url,
            description='React App Bedrock API Gateway URL'
        )

        CfnOutput(
            self, 'React App 3P API ',
            value=self.api_3p_Integration.url,
            description='React App Bedrock API Gateway URL'
        )


        CfnOutput(
            self, 'Bedrock Knowledge Base ID',
            value=kb.knowledge_base_id,
            description='Bedrock Knowledge Base ID' 
        )

        CfnOutput(
            self, 
            "PublicSubnetId",
            value=public_subnet.subnet_id,
            description="Public Subnet ID"
        )

        CfnOutput(
            self, 
            "PrivateSubnetId",
            value=private_subnet.subnet_id,
            description="Private Subnet ID"
        )

        CfnOutput(
            self, 
            "NatGatewayId",
            value=nat_gateway.ref,
            description="NAT Gateway ID"
        )

         # Add outputs for EIP
        CfnOutput(
            self, 
            "ElasticIP",
            value=eip.ref,
            description="Elastic IP Address"
        )

        CfnOutput(
            self, 
            "ElasticIPAllocationId",
            value=eip.attr_allocation_id,
            description="Elastic IP Allocation ID"
        )