import React, { useState, useEffect } from 'react';
import {
  Container,
  Header,
  Select,
  FormField,
  SpaceBetween,
  Box,
  Spinner,
  Table,
  Button,
  Tabs,
  Modal,
} from '@cloudscape-design/components';
import { fetchAuthSession } from '@aws-amplify/auth';
import { useNavigate } from 'react-router-dom';
import { useAuthenticator } from '@aws-amplify/ui-react';

import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { 
  DynamoDBDocumentClient, 
  ScanCommand,
  GetCommand,
  UpdateCommand
} from "@aws-sdk/lib-dynamodb";

declare module 'aws-amplify/auth' {
  function getCurrentUser(): Promise<any>;
  function fetchAuthSession(): Promise<AuthSession>;
}

interface AuthSession {
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken: string;
  };
}

interface DataSourceOption {
  label: string;
  value: string;
}

interface Policyholder {
  id: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: string;
  maritalStatus: string;
  occupation: string;
  locator: string;
  External_Id: string;
}

interface Claim {
  locator: string;
  currentStatus: string;
  incident_type: string;
  incident_summary: string;
  createdTimestamp: string;
}

interface DynamoDBRecord {
  External_Id: string;
  External_PolicyId: string;
}

const REACT_APP_DDBTableNameCustomer = process.env.REACT_APP_DDBTableNameCustomer || '';
const REACT_APP_3PAPI = process.env.REACT_APP_3PAPI || '';
const AWS_REGION = process.env.REACT_APP_AWS_REGION || '';

const ClaimsIntegration: React.FC = () => {
  const navigate = useNavigate();
  const { user, authStatus } = useAuthenticator((context) => [
    context.user,
    context.authStatus
  ]);

  const [selectedDataSource, setSelectedDataSource] = useState<DataSourceOption | null>(null);
  const [policyholders, setPolicyholders] = useState<Policyholder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedItems, setSelectedItems] = useState<Policyholder[]>([]);
  const [customerDetails, setCustomerDetails] = useState<any>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [activeTabId, setActiveTabId] = useState("policies");
  const [claims, setClaims] = useState<Claim[]>([]);
  const [matchedIds, setMatchedIds] = useState<Set<string>>(new Set());

  const handleGoBack = () => {
    navigate('/');
  };

  const dataSources: DataSourceOption[] = [
    { label: 'Socotra', value: 'SOCOTRA' },
  ];

  const checkDynamoDBMatches = async (policyholderData: Policyholder[]) => {
    try {
      const { docClient } = await initializeAWSClients();
      
      const params = {
        TableName: REACT_APP_DDBTableNameCustomer
      };

      const command = new ScanCommand(params);
      const result = await docClient.send(command);
      const dynamoRecords = result.Items as DynamoDBRecord[];

      const matchedIdsSet = new Set<string>();

      policyholderData.forEach(policyholder => {
        const hasMatch = dynamoRecords.some(record => 
          record.External_Id === policyholder.locator || 
          record.External_PolicyId === policyholder.id
        );

        if (hasMatch) {
          matchedIdsSet.add(policyholder.id);
        }
      });

      setMatchedIds(matchedIdsSet);
    } catch (error) {
      console.error('Error checking DynamoDB matches:', error);
    }
  };

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

      const ddbClient = new DynamoDBClient(clientConfig);
      const docClient = DynamoDBDocumentClient.from(ddbClient, {
        marshallOptions: {
          removeUndefinedValues: true,
          convertClassInstanceToMap: true,
        },
      });

      return { docClient };
    } catch (error) {
      console.error('Error initializing AWS clients:', error);
      setError('Failed to initialize AWS services');
      throw error;
    }
  };

  const handleDataSourceChange = async (newDataSource: DataSourceOption) => {
    setSelectedDataSource(newDataSource);
    setLoading(true);
    setError(null);
    setPolicyholders([]);
    setSelectedItems([]);
    setCustomerDetails(null);

    try {
      const response = await fetch(REACT_APP_3PAPI, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dataSource: newDataSource.value
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch data');
      }

      const data = await response.json();
      
      try {
        const parsedData = JSON.parse(data.body);
        if (parsedData.policyholders) {
          const filteredPolicyholders = parsedData.policyholders.filter(
            (policyholder: Policyholder) => policyholder.id && policyholder.id.trim() !== ''
          );
          setPolicyholders(filteredPolicyholders);
          // Check DynamoDB matches after setting policyholders
          await checkDynamoDBMatches(filteredPolicyholders);
        } else {
          setPolicyholders([]);
        }
      } catch (parseError) {
        console.error('Error parsing response body:', parseError);
        setError('Error parsing response data');
      }
    } catch (err) {
      console.error('API Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const columnDefinitions = [
    {
      id: 'id',
      header: 'Customer ID',
      cell: (item: Policyholder) => (
        <Box color={matchedIds.has(item.id) ? "text-status-success" : "text-status-default"}>
          {item.id}
        </Box>
      )
    },
    {
      id: 'firstName',
      header: 'First Name',
      cell: (item: Policyholder) => item.firstName || 'N/A'
    },
    {
      id: 'lastName',
      header: 'Last Name',
      cell: (item: Policyholder) => item.lastName || 'N/A'
    },
    {
      id: 'dateOfBirth',
      header: 'Date of Birth',
      cell: (item: Policyholder) => item.dateOfBirth || 'N/A'
    },
    {
      id: 'gender',
      header: 'Gender',
      cell: (item: Policyholder) => item.gender || 'N/A'
    },
    {
      id: 'maritalStatus',
      header: 'Marital Status',
      cell: (item: Policyholder) => item.maritalStatus || 'N/A'
    },
    {
      id: 'occupation',
      header: 'Occupation',
      cell: (item: Policyholder) => item.occupation || 'N/A'
    },
    {
      id: 'locator',
      header: 'External_Id',
      cell: (item: Policyholder) => (
        <Box color={matchedIds.has(item.id) ? "text-status-success" : "text-status-default"}>
          {item.locator || 'N/A'}
        </Box>
      )
    }
];



  const handleViewDetails = async () => {
    if (!selectedItems.length || !selectedDataSource) return;
  
    setLoading(true);
    setError(null);
  
    try {
      // Single API call to get all data including claims
      const response = await fetch(REACT_APP_3PAPI, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dataSource: selectedDataSource.value,
          policyholderLocator: selectedItems[0].locator
        })
      });
  
      if (!response.ok) {
        throw new Error('Failed to fetch customer details');
      }
  
      const data = await response.json();
      const parsedBody = JSON.parse(data.body);
      const customerData = parsedBody.message;
  
      // Set all the customer details including claims that come from the Lambda response
      setCustomerDetails({
        ...customerData,
        claims: customerData.claims?.map((claim: any) => ({
          locator: claim.locator,
          currentStatus: claim.currentStatus,
          incident_type: claim.incident_type || 'N/A',
          incident_summary: claim.incident_summary || 'N/A',
          createdTimestamp: claim.createdTimestamp,
          policyLocator: claim.policyLocator
        })) || []
      });
  
      setIsModalVisible(true);
    } catch (err) {
      console.error('API Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };
  

  return (
    <Container>
      <SpaceBetween size="l">
        <Header
          variant="h1"
          description="View policyholders information from 3rd Party Claims Systems such as Socotra. For the DEMO purpose, we have the API integration enabled for Socotra. This page wont work if you don't have the Claims system (Socotra) credentials updated as enviornment variables to `gp-fsi-claimsprocessing-3P-integration` Lambda function."
        
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
          Socotra - Sample Integration DEMO 

          
        </Header>

        <FormField label="Select Claims Data Source">
          <Select
            selectedOption={selectedDataSource}
            onChange={({ detail }) =>
              handleDataSourceChange(detail.selectedOption as DataSourceOption)
            }
            options={dataSources}
            placeholder="Choose a data source"
            selectedAriaLabel="Selected"
          />
        </FormField>

        {error && (
          <Box color="error">
            {error}
          </Box>
        )}

        {loading && !isModalVisible ? (
          <Box textAlign="center">
            <Spinner size="large" />
          </Box>
        ) : (
          <SpaceBetween size="l">
            <Table
              columnDefinitions={columnDefinitions}
              items={policyholders}
              loading={loading}
              loadingText="Loading policyholders"
              selectionType="single"
              selectedItems={selectedItems}
              onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
              header={
                <Header
                  counter={`(${policyholders.length})`}
                  actions={
                    <SpaceBetween direction="horizontal" size="xs">
                      <Button
                        onClick={handleViewDetails}
                        disabled={!selectedItems.length}
                      >
                        View Details
                      </Button>
                    </SpaceBetween>
                  }
                >
                  Policyholders
                </Header>
              }
              empty={
                <Box textAlign="center" color="inherit">
                  <b>No policyholders found</b>
                  <Box padding={{ bottom: "s" }}>
                    {selectedDataSource ? 'No policyholders available' : 'Please select a data source'}
                  </Box>
                </Box>
              }
              stickyHeader
              stripedRows
              variant="full-page"
            />
          </SpaceBetween>
        )}

        <Modal
          visible={isModalVisible}
          onDismiss={() => setIsModalVisible(false)}
          header={`Customer Details ${selectedItems[0]?.firstName ? `- ${selectedItems[0].firstName} ${selectedItems[0].lastName}` : ''}`}
          size="large"
        >
          <SpaceBetween size="l">
            {loading ? (
              <Box textAlign="center">
                <Spinner size="large" />
              </Box>
            ) : (
              <Tabs
                activeTabId={activeTabId}
                onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
                tabs={[
                  {
                    id: "policies",
                    label: `Policies (${customerDetails?.policies?.length || 0})`,
                    content: (
                      <Table
                        columnDefinitions={[
                          {
                            id: 'policyId',
                            header: 'Policy ID',
                            cell: (item: any) => item.policyId
                          },
                          {
                            id: 'product',
                            header: 'Product',
                            cell: (item: any) => item.product
                          },
                          {
                            id: 'term',
                            header: 'Term',
                            cell: (item: any) => item.term
                          },
                          {
                            id: 'status',
                            header: 'Status',
                            cell: (item: any) => item.status === 'N/A' ? 'Pending' : item.status
                          }
                        ]}
                        items={customerDetails?.policies || []}
                        loading={loading}
                        loadingText="Loading policies"
                        header={
                          <Header
                            counter={`(${customerDetails?.policies?.length || 0})`}
                          >
                            Policies
                          </Header>
                        }
                        empty={
                          <Box textAlign="center" color="inherit">
                            <b>No policies found</b>
                          </Box>
                        }
                        stickyHeader
                        stripedRows
                      />
                    )
                  },
                  {
                    id: "invoices",
                    label: `Invoices (${customerDetails?.invoices?.length || 0})`,
                    content: (
                      <Table
                        columnDefinitions={[
                          {
                            id: 'invoiceId',
                            header: 'Invoice ID',
                            cell: (item: any) => item.invoiceId
                          },
                          {
                            id: 'type',
                            header: 'Type',
                            cell: (item: any) => {
                              const type = item.type.replace(/([A-Z])/g, ' $1').trim();
                              return type.charAt(0).toUpperCase() + type.slice(1);
                            }
                          },
                          {
                            id: 'billingPeriod',
                            header: 'Billing Period',
                            cell: (item: any) => item.billingPeriod
                          },
                          {
                            id: 'dateCreated',
                            header: 'Date Created',
                            cell: (item: any) => item.dateCreated === '1970-01-01' ? 'Pending' : item.dateCreated
                          },
                          {
                            id: 'dueDate',
                            header: 'Due Date',
                            cell: (item: any) => item.dueDate
                          },
                          {
                            id: 'total',
                            header: 'Total',
                            cell: (item: any) => `$${Number(item.total).toFixed(2)}`
                          },
                          {
                            id: 'status',
                            header: 'Status',
                            cell: (item: any) => item.status === 'N/A' ? 'Pending' : item.status
                          }
                        ]}
                        items={customerDetails?.invoices || []}
                        loading={loading}
                        loadingText="Loading invoices"
                        header={
                          <Header
                            counter={`(${customerDetails?.invoices?.length || 0})`}
                          >
                            Invoices
                          </Header>
                        }
                        empty={
                          <Box textAlign="center" color="inherit">
                            <b>No invoices found</b>
                          </Box>
                        }
                        stickyHeader
                        stripedRows
                      />
                    )
                  },
                  {
                    id: "claims",
                    label: `Claims (${customerDetails?.claims?.length || 0})`,
                    content: (
                      <Table
                        columnDefinitions={[
                          {
                            id: 'locator',
                            header: 'Claim Number',
                            cell: (item: Claim) => item.locator || 'N/A'
                          },
                          {
                            id: 'currentStatus',
                            header: 'Status',
                            cell: (item: Claim) => 
                              item.currentStatus 
                                ? item.currentStatus.charAt(0).toUpperCase() + item.currentStatus.slice(1)
                                : 'N/A'
                          },
                          {
                            id: 'incident_type',
                            header: 'Incident Type',
                            cell: (item: Claim) => item.incident_type || 'N/A'
                          },
                          {
                            id: 'incident_summary',
                            header: 'Incident Summary',
                            cell: (item: Claim) => item.incident_summary || 'N/A'
                          },
                          {
                            id: 'createdTimestamp',
                            header: 'Created Date',
                            cell: (item: Claim) => 
                              item.createdTimestamp 
                                ? new Date(item.createdTimestamp).toLocaleString()
                                : 'N/A'
                          },
                          {
                            id: 'policyLocator',
                            header: 'Policy ID',
                            cell: (item: Claim) => item.policyLocator || 'N/A'
                          }
                        ]}
                        items={customerDetails?.claims || []}
                        loading={loading}
                        loadingText="Loading claims"
                        header={
                          <Header
                            counter={`(${customerDetails?.claims?.length || 0})`}
                          >
                            Claims
                          </Header>
                        }
                        empty={
                          <Box textAlign="center" color="inherit">
                            <b>No claims found</b>
                            <Box padding={{ bottom: "s" }}>
                              No claims available for this customer
                            </Box>
                          </Box>
                        }
                        stickyHeader
                        stripedRows
                      />
                    )
                  }
                ]}
              />
            )}
          </SpaceBetween>
        </Modal>
      </SpaceBetween>
      
    </Container>
  );
};

export default ClaimsIntegration;
