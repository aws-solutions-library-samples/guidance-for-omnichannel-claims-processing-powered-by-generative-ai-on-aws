import { Amplify } from 'aws-amplify';
import { fetchAuthSession } from '@aws-amplify/auth';
import { getCurrentUser } from '@aws-amplify/auth';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthenticator } from '@aws-amplify/ui-react';
import {
  Table,
  Box,
  SpaceBetween,
  Container,
  Header,
  ColumnLayout,
  Button,
  Alert,
  Spinner,
  Link,
  FormField,
  Select,
  Input,
  Textarea,
  Grid,
  Tabs,
  StatusIndicator
} from '@cloudscape-design/components';
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { 
  DynamoDBDocumentClient, 
  ScanCommand,
  GetCommand,
  UpdateCommand
} from "@aws-sdk/lib-dynamodb";


interface AuthSession {
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken: string;
  };
}

declare module 'aws-amplify/auth' {
  function getCurrentUser(): Promise<any>;
  function fetchAuthSession(): Promise<AuthSession>;
}

  // Add this function inside your component
  const handleGoBack = () => {
    navigate('/');
  };


// Types
interface DetailedRecord {
  CaseNumber: string;
  CustomerName: string;
  CarMake_Model: string;
  case_status: string;
  VehiclceAnalysis?: any;
  [key: string]: any;
}

interface ImageUrls {
  [key: string]: string;
}

interface ImageStates {
  [key: string]: boolean;
}

interface ImageErrors {
  [key: string]: string | null;
}

interface BucketInfo {
  bucket: string;
  key: string;
}

interface VehicleAnalysis {
  bucket?: string;
  key?: string;
  analysis_data?: string;
}

// Environment variables
const AWS_REGION = process.env.REACT_APP_AWS_REGION || '';
const REACT_APP_DDBTableNameClaim = process.env.REACT_APP_DDBTableNameClaim || '';
const REACT_APP_NOTIFICATION_SQS_QUEUE_URL = process.env.REACT_APP_NOTIFICATION_SQS_QUEUE_URL || '';



const Adjudicate: React.FC = () => {
  const navigate = useNavigate();
  const { user, authStatus } = useAuthenticator((context) => [
    context.user,
    context.authStatus
  ]);

  // State declarations
  const [items, setItems] = useState<DetailedRecord[]>([]);
  const [selectedItem, setSelectedItem] = useState<DetailedRecord | null>(null);
  const [detailedRecord, setDetailedRecord] = useState<DetailedRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [decision, setDecision] = useState<string>('');
  const [comments, setComments] = useState<string>('');
  const [claimAmount, setClaimAmount] = useState<string>('');
  const [activeTabId, setActiveTabId] = useState('details');
  const [imageUrls, setImageUrls] = useState<ImageUrls>({});
  const [imageLoadingStates, setImageLoadingStates] = useState<ImageStates>({});
  const [imageErrors, setImageErrors] = useState<ImageErrors>({});
  const [bucketInfo, setBucketInfo] = useState<BucketInfo | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Effect for loading basic info image
  useEffect(() => {
    if (bucketInfo && bucketInfo.bucket && bucketInfo.key) {
      const imageId = `${bucketInfo.bucket}-${bucketInfo.key}`;
      loadImageUrl(bucketInfo.bucket, bucketInfo.key, imageId);
    }
  }, [bucketInfo]);

  // Effect for loading vehicle analysis images
  useEffect(() => {
    if (detailedRecord?.VehiclceAnalysis) {
      let vehicleAnalysisData;
      try {
        vehicleAnalysisData = typeof detailedRecord.VehiclceAnalysis === 'string'
          ? JSON.parse(detailedRecord.VehiclceAnalysis)
          : detailedRecord.VehiclceAnalysis;

        const analysisMap = vehicleAnalysisData.M || vehicleAnalysisData;
        
        Object.entries(analysisMap).forEach(([vehicleKey, vehicleData]) => {
          const vehicleMap = vehicleData.M || vehicleData;
          
          Object.entries(vehicleMap).forEach(([s3Path, analysisData]) => {
            const s3PathMatch = s3Path.match(/s3:\/\/([^\/]+)\/(.+)/);
            if (s3PathMatch) {
              const bucket = s3PathMatch[1];
              const key = s3PathMatch[2];
              const imageId = `${bucket}-${key}`;
              loadImageUrl(bucket, key, imageId);
            }
          });
        });
      } catch (e) {
        console.error('Error parsing VehiclceAnalysis:', e);
      }
    }
  }, [detailedRecord]);

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

      const s3Client = new S3Client(clientConfig);
      const sqsClient = new SQSClient(clientConfig);
      const ddbClient = new DynamoDBClient(clientConfig);
      const docClient = DynamoDBDocumentClient.from(ddbClient, {
        marshallOptions: {
          removeUndefinedValues: true,
          convertClassInstanceToMap: true,
        },
      });

      return { s3Client, sqsClient, docClient };
    } catch (error) {
      console.error('Error initializing AWS clients:', error);
      setError('Failed to initialize AWS services');
      throw error;
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const currentUser = await getCurrentUser();
        if (currentUser) {
          setAuthLoading(false);
          fetchData();
        } else {
          navigate('/login');
        }
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

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const { docClient } = await initializeAWSClients();
      
      const command = new ScanCommand({
        TableName: REACT_APP_DDBTableNameClaim
      });

      const response = await docClient.send(command);
      
      if (response.Items) {
        setItems(response.Items as DetailedRecord[]);
      }
    } catch (err) {
      console.error('Error fetching claims:', err);
      setError(err instanceof Error ? err.message : 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  };

  const extractBucketInfo = (vehicleAnalysis: VehicleAnalysis | null): BucketInfo | null => {
    if (!vehicleAnalysis) return null;

    let analysisData;
    try {
      if (typeof vehicleAnalysis.analysis_data === 'string') {
        analysisData = JSON.parse(vehicleAnalysis.analysis_data);
      }
    } catch (error) {
      console.error('Error parsing analysis data:', error);
      return null;
    }

    if (vehicleAnalysis.bucket && vehicleAnalysis.key) {
      return {
        bucket: vehicleAnalysis.bucket,
        key: vehicleAnalysis.key
      };
    }

    return null;
  };

  const fetchDetailedRecord = async (caseNumber: string) => {
    try {
      setLoadingDetails(true);
      setError(null);

      const { docClient } = await initializeAWSClients();

      const command = new GetCommand({
        TableName: REACT_APP_DDBTableNameClaim,
        Key: {
          CaseNumber: caseNumber
        }
      });

      const response = await docClient.send(command);
      
      if (response.Item) {
        setDetailedRecord(response.Item as DetailedRecord);
        
        if (response.Item.VehiclceAnalysis) {
          try {
            const vehicleAnalysis = typeof response.Item.VehiclceAnalysis === 'string' 
              ? JSON.parse(response.Item.VehiclceAnalysis)
              : response.Item.VehiclceAnalysis;
              
            const bucketData = extractBucketInfo(vehicleAnalysis);
            setBucketInfo(bucketData);
          } catch (parseError) {
            console.error("Error parsing vehicle analysis:", parseError);
            setBucketInfo(null);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching detailed record:', error);
      setError('Failed to load claim details');
    } finally {
      setLoadingDetails(false);
    }
  };

  const loadImageUrl = async (bucket: string, key: string, imageId: string): Promise<void> => {
    setImageLoadingStates(prev => ({ ...prev, [imageId]: true }));
    setImageErrors(prev => ({ ...prev, [imageId]: null }));
    
    try {
      const { s3Client } = await initializeAWSClients();
      const command = new GetObjectCommand({
        Bucket: bucket,
        Key: key
      });
      const url = await getSignedUrl(s3Client, command, { expiresIn: 3600 });
      setImageUrls(prev => ({ ...prev, [imageId]: url }));
    } catch (error) {
      console.error("Error loading image:", error);
      setImageErrors(prev => ({ 
        ...prev, 
        [imageId]: "Failed to load image. Please try again later."
      }));
    } finally {
      setImageLoadingStates(prev => ({ ...prev, [imageId]: false }));
    }
  };

  const handleDecisionSubmit = async () => {
    try {
      setSubmitting(true);
      setError(null);
      setSuccessMessage(null);

      if (!detailedRecord?.CaseNumber) {
        throw new Error('No case number selected');
      }

      const { docClient } = await initializeAWSClients();

      const command = new UpdateCommand({
        TableName: REACT_APP_DDBTableNameClaim,
        Key: {
          CaseNumber: detailedRecord.CaseNumber
        },
        UpdateExpression: 'SET case_status = :status, comments = :comments, claim_amount = :amount',
        ExpressionAttributeValues: {
          ':status': decision,
          ':comments': comments,
          ':amount': claimAmount
        },
        ReturnValues: 'ALL_NEW'
      });

      await docClient.send(command);

      const claimDetails = {
        CaseNumber: detailedRecord.CaseNumber,
        amount:claimAmount,
        decision: decision,
        comments: comments
      };

      await sendSQSMessage(claimDetails);
      
      setSuccessMessage(
        decision === 'Approved'
          ? `Claim ${detailedRecord.CaseNumber} has been approved successfully`
          : `Claim ${detailedRecord.CaseNumber} has been rejected`
      );

      await fetchData();
      
      setTimeout(() => {
        window.location.reload();
      }, 2000);

    } catch (err) {
      console.error('Error submitting decision:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit decision');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectionChange = ({ detail }: { detail: { selectedItems: DetailedRecord[] } }) => {
    const selected = detail.selectedItems[0] || null;
    setSelectedItem(selected);
    if (selected) {
      fetchDetailedRecord(selected.CaseNumber);
    } else {
      setDetailedRecord(null);
      setBucketInfo(null);
    }
  };

  const getStatusType = (status: string | undefined): string => {
    switch (status?.toLowerCase()) {
      case 'approved': return 'success';
      case 'pending':
      case 'in review': return 'pending';
      case 'rejected': return 'error';
      default: return 'info';
    }
  };

  const columnDefinitions = [
    {
      id: "CaseNumber",
      header: "Case Number",
      cell: (item: DetailedRecord) => (
        <Link onFollow={() => {
          setSelectedItem(item);
          fetchDetailedRecord(item.CaseNumber);
        }}>
          {item.CaseNumber || '-'}
        </Link>
      ),
      sortingField: "CaseNumber"
    },
    {
      id: "CustomerName",
      header: "Customer Name",
      cell: (item: DetailedRecord) => item.CustomerName || '-',
      sortingField: "CustomerName"
    },
    {
      id: "CarMake_Model",
      header: "Vehicle",
      cell: (item: DetailedRecord) => item.CarMake_Model || '-',
      sortingField: "CarMake_Model"
    },
    {
      id: "case_status",
      header: "Status",
      cell: (item: DetailedRecord) => (
        <StatusIndicator type={getStatusType(item.case_status)}>
          {item.case_status || 'Unknown'}
        </StatusIndicator>
      ),
      sortingField: "case_status"
    }
  ];

  if (authLoading || authStatus === 'configuring') {
    return (
      <Container>
        <Spinner size="large" />
      </Container>
    );
  }

  const renderDetailedView = () => {
      if (!detailedRecord) return null;
  
      return (
        <Container
          header={
            <Header
              variant="h2"
              description="Detailed claim information. Only those claims with the status 'Review' will have an option to take a decision."
            >
              Claim Details - {selectedItem?.CaseNumber}
            </Header>
          }
        >
          {loadingDetails ? (
            <Box textAlign="center">Loading detailed information...</Box>
          ) : (
            <Tabs
              tabs={[
                {
                  label: "Basic Information",
                  id: "basic",
                  content: renderBasicInfo()
                },
                {
                  label: "Vehicle Analysis",
                  id: "analysis",
                  content: renderVehicleAnalysis()
                },
                {
                  label: "AI Summary",
                  id: "ai",
                  content: renderAISummary()
                }
              ]}
            />
          )}
        </Container>
      );
    };
  
  
    const renderBasicInfo = () => {
      const basicFields = [
        { key: 'CaseNumber', label: 'Case Number' },
        { key: 'CustomerName', label: 'Customer Name' },
        { key: 'CustomerEmail', label: 'Email' },
        { key: 'CustomerPhone', label: 'Phone' },
        { key: 'CarMake_Model', label: 'Vehicle' },
        { key: 'LossDate', label: 'Loss Date' },
        { key: 'LossLocation', label: 'Loss Location' },
        { key: 'case_status', label: 'Status' }
      ];
  
      const imageId = bucketInfo ? `${bucketInfo.bucket}-${bucketInfo.key}` : null;
  
      return (
        <SpaceBetween size="l">
          <ColumnLayout columns={3} variant="text-grid">
            {basicFields.map(({ key, label }) => (
              <div key={key}>
                <Box variant="awsui-key-label">{label}</Box>
                <div>{detailedRecord?.[key] || '-'}</div>
              </div>
            ))}
          </ColumnLayout>
          {renderDecisionContainer()}
        </SpaceBetween>
      );
    };

    const formatVehicleKey = (key: string) => {
      return key.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      ).join(' ');
    };
  
    // Function to send message to SQS
const sendSQSMessage = async (claimDetails: ClaimDetails) => {
  try {
    const { sqsClient } = await initializeAWSClients();
    const params = {
      QueueUrl: REACT_APP_NOTIFICATION_SQS_QUEUE_URL,
      MessageBody: JSON.stringify(claimDetails),
      MessageAttributes: {
        "MessageType": {
          DataType: "String",
          StringValue: "NewClaim"
        },
        "Timestamp": {
          DataType: "String",
          StringValue: new Date().toISOString()
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

      const renderDecisionContainer = () => {
        if (selectedItem.case_status === "Review" ) 
    
        return (
          <Container header={<Header variant="h2">Make a decision on this claim</Header>}>
            <SpaceBetween size="l">
              <FormField label="Decision">
                <Select
                  selectedOption={
                    decision
                      ? { label: decision, value: decision }
                      : null
                  }
                  onChange={({ detail }) =>
                    setDecision(detail.selectedOption.value)
                  }
                  options={[
                    { label: "Approve", value: "Approved" },
                    { label: "Reject", value: "Rejected" },
                    { label: "Need More Info", value: "More Info Needed" }
                  ]}
                  placeholder="Select a decision"
                />
              </FormField>
    
              <FormField label="Claim Amount">
                <Input
                  type="number"
                  value={claimAmount}
                  onChange={({ detail }) => setClaimAmount(detail.value)}
                  placeholder="Enter claim amount"
                />
              </FormField>
    
              <FormField label="Comments">
                <Textarea
                  value={comments}
                  onChange={({ detail }) => setComments(detail.value)}
                  placeholder="Enter your comments"
                />
              </FormField>
    
              <Button
                variant="primary"
                onClick={handleDecisionSubmit}
                loading={submitting}
                disabled={!decision || submitting}
              >
                Submit Decision
              </Button>
            </SpaceBetween>
          </Container>
        );
      };
    
  
    const renderVehicleAnalysis = () => {
      if (!detailedRecord?.VehiclceAnalysis) {
        return <Box variant="p">No vehicle analysis data available</Box>;
      }
  
      let vehicleAnalysisData;
      try {
        vehicleAnalysisData = typeof detailedRecord.VehiclceAnalysis === 'string'
          ? JSON.parse(detailedRecord.VehiclceAnalysis)
          : detailedRecord.VehiclceAnalysis;
      } catch (e) {
        console.error('Error parsing VehiclceAnalysis:', e);
        return <Box variant="p">Error parsing vehicle analysis data</Box>;
      }
  
      const analysisMap = vehicleAnalysisData.M || vehicleAnalysisData;
      
      return (
        <SpaceBetween size="l">
          {Object.entries(analysisMap).map(([vehicleKey, vehicleData]) => {
            const vehicleMap = vehicleData.M || vehicleData;
            
            return Object.entries(vehicleMap).map(([s3Path, analysisData]) => {
              const s3PathMatch = s3Path.match(/s3:\/\/([^\/]+)\/(.+)/);
              const bucket = s3PathMatch ? s3PathMatch[1] : '';
              const key = s3PathMatch ? s3PathMatch[2] : '';
              const analysisText = analysisData.S || analysisData;
              const imageId = `${bucket}-${key}`;
  
              return (
                <Container
                  key={`${vehicleKey}-${s3Path}`}
                  header={<Header variant="h3">{formatVehicleKey(vehicleKey)}</Header>}
                >
                  <Grid
                    gridDefinition={[
                      { colspan: { default: 12, xxs: 6 } },
                      { colspan: { default: 12, xxs: 6 } }
                    ]}
                  >
                    <SpaceBetween size="l">
                      <div>
                        <Box variant="awsui-key-label">Image Location</Box>
                        <SpaceBetween size="xs">
                          <div>
                            <Box variant="small">
                              <strong>Bucket:</strong> {bucket}
                            </Box>
                          </div>
                          <div>
                            <Box variant="small">
                              <strong>Key:</strong> {key}
                            </Box>
                          </div>
                        </SpaceBetween>
                      </div>
                      <div>
                        <Box variant="awsui-key-label">Analysis</Box>
                        <Box variant="p">{analysisText}</Box>
                      </div>
                    </SpaceBetween>
                    <Container>
                      {imageLoadingStates[imageId] ? (
                        <Box textAlign="center" padding="l">
                          <Spinner size="normal" />
                          <Box variant="p">Loading image...</Box>
                        </Box>
                      ) : imageErrors[imageId] ? (
                        <Box textAlign="center" color="error" padding="l">
                          <Box variant="p">{imageErrors[imageId]}</Box>
                          <Button 
                            onClick={() => loadImageUrl(bucket, key, imageId)}
                            variant="link"
                          >
                            Retry loading image
                          </Button>
                        </Box>
                      ) : (
                        <img
                          src={imageUrls[imageId]}
                          alt={`Vehicle ${formatVehicleKey(vehicleKey)}`}
                          style={{
                            maxWidth: '100%',
                            height: 'auto',
                            display: 'block',
                            margin: '0 auto'
                          }}
                          onError={(e) => {
                            console.error('Error loading image');
                            setImageErrors(prev => ({ 
                              ...prev, 
                              [imageId]: "Failed to display image. Please try again."
                            }));
                          }}
                        />
                      )}
                    </Container>
                  </Grid>
                </Container>
              );
            });
          })}
        </SpaceBetween>
      );
    };
  
    const renderAISummary = () => {
      return (
        <SpaceBetween size="l">
          {detailedRecord?.GenAI_Summary && (
            <Container header={<Header variant="h3">AI Summary</Header>}>
              <Box variant="p">{detailedRecord.GenAI_Summary}</Box>
            </Container>
          )}
          {detailedRecord?.Combined_vehicle_image_analysis_output && (
            <Container header={<Header variant="h3">Combined Analysis</Header>}>
              <Box variant="p">{detailedRecord.Combined_vehicle_image_analysis_output}</Box>
            </Container>
          )}
        </SpaceBetween>
      );
    };
  
    return (
      <SpaceBetween size="l">
      <Container
        header={
          <Header
            variant="h1"
            actions={
              <Button
                variant="link"
                iconName="arrow-left"
                onClick={handleGoBack}
                className="back-button"
              >
                Back to Home
              </Button>
            }
          >
            Claims Adjudication Page
          </Header>
        }
      >
        <SpaceBetween size="l">
          {error && (
            <Alert
              type="error"
              header="Error"
              dismissible
            >
              {error}
            </Alert>
          )}
  
          {/* Claims Table with improved styling */}
          <Table
            loading={loading}
            loadingText="Loading claims..."
            items={items}
            columnDefinitions={columnDefinitions}
            header={
              <Header
                variant="h2"
                description="Select a claim to view or process"
                actions={
                  <Button
                    onClick={fetchData}
                    iconName="refresh"
                    variant="primary"
                  >
                    Refresh Claims
                  </Button>
                }
              >
                Claims List
              </Header>
            }
            empty={
              <Box
                margin={{ vertical: "xs" }}
                textAlign="center"
                color="inherit"
              >
                <b>No claims found</b>
                <Box
                  padding={{ bottom: "s" }}
                  variant="p"
                  color="inherit"
                >
                  No claims are available for adjudication.
                </Box>
              </Box>
            }
            selectionType="single"
            selectedItems={selectedItem ? [selectedItem] : []}
            onSelectionChange={handleSelectionChange}
            wrapLines
            stripedRows
            stickyHeader
            resizableColumns
            variant="container"
          />
        </SpaceBetween>
      </Container>
        {selectedItem && renderDetailedView()}
      </SpaceBetween>
    );
  };

export default Adjudicate;
