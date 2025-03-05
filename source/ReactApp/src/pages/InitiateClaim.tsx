import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PutCommand } from '@aws-sdk/lib-dynamodb';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient,GetCommand } from '@aws-sdk/lib-dynamodb';
import { getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';
import { useAuthenticator } from '@aws-amplify/ui-react';
import {
  Alert,
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  Select,
  Spinner,
  SpaceBetween,
  Textarea,
} from '@cloudscape-design/components';
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

const AWS_REGION = process.env.REACT_APP_AWS_REGION || '';
const REACT_APP_DDBTableNameClaim = process.env.REACT_APP_DDBTableNameClaim || '';
const REACT_APP_DDBTableNameCustomer = process.env.REACT_APP_DDBTableNameCustomer || '';
const REACT_APP_3P_SQS_QUEUE_URL = process.env.REACT_APP_3P_SQS_QUEUE_URL || '';
const REACT_APP_NOTIFICATION_SQS_QUEUE_URL = process.env.REACT_APP_NOTIFICATION_SQS_QUEUE_URL || '';

const formatDateTimeForDB = (dateTimeString: string): string => {
  return new Date(dateTimeString).toISOString();
};

const InitiateClaim = () => {
  const navigate = useNavigate();
  const { authStatus } = useAuthenticator(context => [context.authStatus]);
  const [authLoading, setAuthLoading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showOtpVerification, setShowOtpVerification] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [verifiedOtp, setVerifiedOtp] = useState('');
  const [currentUser, setCurrentUser] = useState(null);


  
    const [formData, setFormData] = useState({
      policyNumber: '',
      otp: '',
      otpVerified: false,
      customerName: '',
      customerEmail: '',
      customerPhone: '',
      carMakeModel: '',
      vehicles: [],
      lossDate: '',
      lossLocation: '',
      details: '',
      incidentReport: '',
      driverName: ''
    });
  

  // ... rest of your state declarations ...

  const initializeAWSClients = async () => {
    try {
      const { credentials } = await fetchAuthSession();
      
      if (!credentials) {
        throw new Error('No credentials available');
      }

      const clientConfig = {
        region: AWS_REGION,
        credentials: {
          accessKeyId: credentials.accessKeyId,
          secretAccessKey: credentials.secretAccessKey,
          sessionToken: credentials.sessionToken
        }
      };

      const sqsClient = new SQSClient(clientConfig);
      const ddbClient = new DynamoDBClient(clientConfig);
      const docClient = DynamoDBDocumentClient.from(ddbClient, {
        marshallOptions: {
          removeUndefinedValues: true,
          convertClassInstanceToMap: true,
        },
      });

      return { docClient,sqsClient };
    } catch (error) {
      console.error('Error initializing AWS clients:', error);
      setError('Failed to initialize AWS services');
      throw error;
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await getCurrentUser();
        setCurrentUser(user);
        setAuthLoading(false);
      } catch (error) {
        console.error('Authentication error:', error);
        navigate('/login');
      }
    };

    if (authStatus === 'authenticated') {
      checkAuth();
    } else if (authStatus === 'unauthenticated') {
      navigate('/login');
    }
  }, [authStatus, navigate]);

  const handleGoBack = () => {
    navigate('/');
  };

  const verifyPolicyNumber = async () => {
    try {
      setLoading(true);
      setError('');
  
      if (!formData.policyNumber) {
        setError('Please enter a policy number');
        return;
      }
  
      const { docClient } = await initializeAWSClients();
  
      const getCommand = new GetCommand({
        TableName: REACT_APP_DDBTableNameCustomer,
        Key: {
          Policy_VIN: formData.policyNumber
        }
      });
  
      const response = await docClient.send(getCommand);
      
      if (!response.Item) {
        setError('Policy number not found. Please check and try again.');
        return;
      }
  
      const customerData = response.Item;
  
      // Generate OTP
      const generatedOtp = generateRandomOtp();
      setVerifiedOtp(generatedOtp);
      
      // Update form with customer data
      setFormData(prev => ({
        ...prev,
        customerName: customerData.CustomerName || '',
        customerEmail: customerData.CustomerEmail || '',
        customerPhone: customerData.CustomerPhone || '',
        External_Id: customerData.External_Id || '',
        vehicles: customerData.Vehicles?.map((vehicle: string) => ({
          label: vehicle,
          value: vehicle
        })) || []
      }));
  
    // Send OTP notification to SQS
    await sendCustNotification(
      customerData.CustomerPhone,
      `Please enter this ${generatedOtp} OTP code to verify your identity`,
      `${formData.policyNumber}-${generatedOtp}`
    );

  
      setShowOtpVerification(true);
  
    } catch (error) {
      console.error('Error verifying policy number:', error);
      setError(
        error instanceof Error 
          ? `Error verifying policy number: ${error.message}`
          : 'Error verifying policy number. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };
  

  const generateRandomOtp = () => {
    return Math.floor(100000 + Math.random() * 900000).toString();
  };
  
  const sendCustNotification = async (customerPhone: string, Message: string, CaseNumber: string) => {
    try {
      const { sqsClient } = await initializeAWSClients();
      
      const notificationMessage = {
        CustomerPhone: customerPhone,
        Message: Message,
        CaseNumber: CaseNumber 
      };
  
      const params = {
        QueueUrl: REACT_APP_NOTIFICATION_SQS_QUEUE_URL,
        MessageBody: JSON.stringify(notificationMessage),
        MessageAttributes: {
          "MessageType": {
            DataType: "String",
            StringValue: "OTPNotification"
          }
        }
      };
  
      const command = new SendMessageCommand(params);
      await sqsClient.send(command);
      console.log("Successfully sent OTP notification to SQS");
    } catch (error) {
      console.error("Error sending OTP notification:", error);
      throw error;
    }
  };
  
  const verifyOtp = async (e) => {
    e.preventDefault();
    try {
      if (!formData.otp) {
        setError('Please enter OTP');
        return;
      }
  
      if (formData.otp.length !== 6 || !/^\d+$/.test(formData.otp)) {
        setError('Please enter a valid 6-digit OTP');
        return;
      }
  
      // Check if entered OTP matches the generated OTP or is the test OTP (999999)
      if (formData.otp === verifiedOtp || formData.otp === '999999') {
        setFormData(prev => ({ 
          ...prev, 
          otpVerified: true
        }));
        setShowForm(true);
        setError('');
      } else {
        setError('Invalid OTP. Please try again.');
      }
    } catch (error) {
      console.error('Error verifying OTP:', error);
      setError('Error verifying OTP. Please try again.');
    }
  };
  

    const sendSQSMessage = async (claimDetails: ClaimDetails) => {
      try {
       
        const { sqsClient } = await initializeAWSClients();
        const params = {
          QueueUrl: REACT_APP_3P_SQS_QUEUE_URL,
          MessageBody: JSON.stringify(claimDetails),
          MessageAttributes: {
            "MessageType": {
              DataType: "String",
              StringValue: "NewClaim"
            }
          }
        };
    
        const command = new SendMessageCommand(params);
        await sqsClient.send(command);
        console.log("Successfully sent message to SQS");
      } catch (error) {
        console.error("Error sending message to SQS:", error);
        throw error;
      }
    };

    const handleSubmit = async () => {
      try {
        setLoading(true);
        setError('');
  
        if (!formData.otpVerified) {
          setError('Please verify your policy number first.');
          return;
        }
  
        const requiredFields = {
          carMakeModel: 'Vehicle',
          lossDate: 'Loss Date and Time',
          lossLocation: 'Loss Location'
        };
  
        const missingFields = Object.entries(requiredFields)
          .filter(([key]) => !formData[key])
          .map(([_, label]) => label);
  
        if (missingFields.length > 0) {
          setError(`Please fill in the following required fields: ${missingFields.join(', ')}`);
          return;
        }
  
        const { docClient } = await initializeAWSClients();
  
        const randomNum = Math.floor(100000 + Math.random() * 900000).toString().padStart(6, '0');
        const caseNumber = `${formData.policyNumber}-${randomNum}`;
        const timestamp = new Date().toISOString();
  
        const claimItem = {
          CaseNumber: caseNumber,
          PolicyNumber: formData.policyNumber,
          CustomerName: formData.customerName,
          CustomerEmail: formData.customerEmail,
          CustomerPhone: formData.customerPhone,
          CarMake_Model: formData.carMakeModel,
          LossDate: formatDateTimeForDB(formData.lossDate),
          LossLocation: formData.lossLocation,
          Details: formData.details || 'No details provided',
          IncidentReport: formData.incidentReport || 'No report number',
          DriverName: formData.driverName || formData.customerName,
          External_Id: formData.External_Id,
          VehiclceAnalysis:{},
          case_status: 'Pending for user documents',
          CreatedAt: timestamp,
          UpdatedAt: timestamp,
          CreatedBy: currentUser?.username
        };

  
        const command = new PutCommand({
          TableName: REACT_APP_DDBTableNameClaim,
          Item: claimItem
        });
  
        await docClient.send(command);

        // Send message to SQS for 3rd party Integration
        await sendSQSMessage(claimItem);
        
        // Just set the success message without any other state changes or navigation
        setSuccessMessage(`Claim submitted successfully! Your case number is: ${caseNumber}`);
  
      } catch (error) {
        console.error('Error submitting claim:', error);
        setError(
          error instanceof Error 
            ? `Error submitting claim: ${error.message}` 
            : 'Error submitting claim. Please try again.'
        );
      } finally {
        setLoading(false);
      }
    };

  if (authLoading) {
    return (
      <Container>
        <Spinner size="large" />
      </Container>
    );
  }

  return (
    <Container>
      <SpaceBetween size="l">
        <Header
          variant="h1"
          description="Submit a new insurance claim"
          actions={
            <Button onClick={handleGoBack}>Back to Home</Button>
          }
        >
          Initiate New Claim
        </Header>

        {successMessage && (
          <Alert
            type="success"
            header="Claim Submitted Successfully"
            dismissible={false}
          >
            {successMessage}
            <br />
            Please save this case number for future reference. Use the Upload Documents tab to Upload supporting documents
          </Alert>
        )}

        {error && (
          <Alert type="error" dismissible onDismiss={() => setError('')}>
            {error}
          </Alert>
        )}

        <Form>
          <SpaceBetween size="l">
            {!showForm && (
              <FormField label="Policy Number" description="You can use one of these sample policy numbers: PY1234, PY0001,PY4321, PY4000 to start testing." constraintText="Required">
                
                
                <Input
                  value={formData.policyNumber}
                  onChange={({ detail }) => 
                    setFormData(prev => ({ ...prev, policyNumber: detail.value }))
                  }
                  disabled={showOtpVerification}
                />

                {!showOtpVerification && (
                  <Button 
                    onClick={verifyPolicyNumber}
                    loading={loading}
                  >
                    Verify Policy Number
                  </Button>
                )}
              </FormField>
            )}

            {showOtpVerification && !showForm && (
              <FormField label="Enter OTP" description="If Amazon Connect SMS feature is not enabled, you can use a sample OTP number 999999 for testing. " constraintText="Required">
              
                <Input
                  value={formData.otp}
                  onChange={({ detail }) => 
                    setFormData(prev => ({ ...prev, otp: detail.value }))
                  }
                  type="number"
                />

                <Button onClick={verifyOtp}>Verify OTP</Button>

              </FormField>
            )}

            {showForm && (
              <SpaceBetween size="l">
                {/* Form fields remain the same */}
                <FormField label="Customer Name">
                  <Input 
                    value={formData.customerName} 
                    disabled 
                    description="Retrieved from customer record"
                  />
                </FormField>

                <FormField label="Customer Email">
                  <Input 
                    value={formData.customerEmail} 
                    disabled 
                    description="Retrieved from customer record"
                  />
                </FormField>

                <FormField label="Customer Phone">
                  <Input 
                    value={formData.customerPhone} 
                    disabled 
                    description="Retrieved from customer record"
                  />
                </FormField>

                <FormField label="Vehicle" constraintText="Required">
                  <Select
                    selectedOption={
                      formData.carMakeModel 
                        ? { label: formData.carMakeModel, value: formData.carMakeModel }
                        : null
                    }
                    onChange={({ detail }) => 
                      setFormData(prev => ({ 
                        ...prev, 
                        carMakeModel: detail.selectedOption.value || '' 
                      }))
                    }
                    options={formData.vehicles}
                  />
                </FormField>

                <FormField 
                  label="Loss Date" 
                  constraintText="Required - Cannot be a future date"
                  errorText={formData.lossDate && new Date(formData.lossDate) > new Date() ? "Loss date cannot be in the future" : undefined}
                >
                  <Input
                    type="datetime-local"
                    value={formData.lossDate}
                    onChange={({ detail }) => {
                      const selectedDate = new Date(detail.value);
                      const now = new Date();
                      
                      if (selectedDate > now) {
                        // If future date is selected, either:
                        // Option 1: Set to current date-time
                        setFormData(prev => ({ 
                          ...prev, 
                          lossDate: now.toISOString().slice(0, 16) 
                        }));
                        
                        // OR Option 2: Keep the previous value
                        // setFormData(prev => ({ ...prev }));
                      } else {
                        // If valid date is selected
                        setFormData(prev => ({ 
                          ...prev, 
                          lossDate: detail.value 
                        }));
                      }
                    }}
                    max={new Date().toISOString().slice(0, 16)} // Restrict future dates in date picker
                  />
                </FormField>


                <FormField label="Loss Location" constraintText="Required">
                  <Input
                    value={formData.lossLocation}
                    onChange={({ detail }) => 
                      setFormData(prev => ({ ...prev, lossLocation: detail.value }))
                    }
                  />
                </FormField>

                <FormField label="Driver Name">
                  <Input
                    value={formData.driverName}
                    onChange={({ detail }) => 
                      setFormData(prev => ({ ...prev, driverName: detail.value }))
                    }
                    placeholder={formData.customerName}
                  />
                </FormField>

                <FormField label="Incident Details">
                  <Textarea
                    value={formData.details}
                    onChange={({ detail }) => 
                      setFormData(prev => ({ ...prev, details: detail.value }))
                    }
                  />
                </FormField>

                <FormField label="Incident Report Number">
                  <Input
                    value={formData.incidentReport}
                    onChange={({ detail }) => 
                      setFormData(prev => ({ ...prev, incidentReport: detail.value }))
                    }
                  />
                </FormField>

                <Button
                  variant="primary"
                  onClick={handleSubmit}
                  loading={loading}
                >
                  Submit Claim
                </Button>
              </SpaceBetween>
            )}
          </SpaceBetween>
        </Form>
      </SpaceBetween>
    </Container>
  );
};

export default InitiateClaim;
