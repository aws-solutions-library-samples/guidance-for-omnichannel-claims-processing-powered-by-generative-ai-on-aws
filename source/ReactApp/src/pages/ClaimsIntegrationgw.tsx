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

interface DataSourceOption {
  label: string;
  value: string;
}

interface GuidewireClaim {
  adjusterName: string;
  claimNumber: string;
  createdTimestamp: string;
  currentStatus: string;
  incident_summary: string;
  incident_type: string;
  insuredName: string;
  locator: string;
  paidAmount: string;
  policyLocator: string;
}

const REACT_APP_3PAPI = process.env.REACT_APP_3PAPI || '';
const AWS_REGION = process.env.REACT_APP_AWS_REGION || '';

const ClaimsIntegrationGW: React.FC = () => {
  const navigate = useNavigate();
  const { user, authStatus } = useAuthenticator((context) => [
    context.user,
    context.authStatus
  ]);

  const [selectedDataSource, setSelectedDataSource] = useState<DataSourceOption>({ 
    label: 'Guidewire', 
    value: 'guidewire' 
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [claims, setClaims] = useState<GuidewireClaim[]>([]);

  const dataSourceOptions: DataSourceOption[] = [
    { label: 'Guidewire', value: 'guidewire' },
  ];



  const handleGoBack = () => {
    navigate('/');
  };

  const columnDefinitions = [
    {
      id: 'policyLocator',
      header: 'Policy ID',
      cell: (item: GuidewireClaim) => item.policyLocator || 'N/A'
    },
    {
      id: 'claimNumber',
      header: 'Claim Number',
      cell: (item: GuidewireClaim) => item.claimNumber || 'N/A',
      sortingField: 'claimNumber'
    },
    {
      id: 'insuredName',
      header: 'Insured Name',
      cell: (item: GuidewireClaim) => item.insuredName || 'N/A',
      sortingField: 'insuredName'
    },
    {
      id: 'currentStatus',
      header: 'Status',
      cell: (item: GuidewireClaim) => (
        <Box color={item.currentStatus === 'Open' ? 'text-status-info' : 'text-status-success'}>
          {item.currentStatus || 'N/A'}
        </Box>
      )
    },
    {
      id: 'incident_type',
      header: 'Incident Type',
      cell: (item: GuidewireClaim) => item.incident_type || 'N/A'
    },
    {
      id: 'adjusterName',
      header: 'Adjuster',
      cell: (item: GuidewireClaim) => item.adjusterName || 'N/A'
    },
    {
      id: 'paidAmount',
      header: 'Paid Amount',
      cell: (item: GuidewireClaim) => (
        <Box textAlign="right">
          ${Number(item.paidAmount).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })}
        </Box>
      )
    },
    {
      id: 'createdTimestamp',
      header: 'Created Date',
      cell: (item: GuidewireClaim) => {
        const date = new Date(item.createdTimestamp);
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
    },
  
    {
      id: 'incident_summary',
      header: 'Summary',
      cell: (item: GuidewireClaim) => item.incident_summary || 'N/A'
    }
  ];

  const handleDataSourceChange = async (newDataSource: DataSourceOption) => {
    console.log('Changing data source to:', newDataSource.label);
    setSelectedDataSource(newDataSource);
    setLoading(true);
    setError(null);
    setClaims([]);
  
    try {
      console.log('Fetching data from API...');
      const response = await fetch(REACT_APP_3PAPI, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          dataSource: newDataSource.value
        })
      });
  
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.statusText}`);
      }
  
      const data = await response.json();
      console.log('Raw API Response:', data);
  
      try {
        // Parse the response body if it's a string
        const parsedData = typeof data.body === 'string' ? JSON.parse(data.body) : data.body;
        console.log('Parsed Claims Data:', parsedData);
  
        // Extract the claims array from the parsed data
        const claimsArray = parsedData.claims || [];
        console.log('Claims Array:', claimsArray);
  
        if (Array.isArray(claimsArray)) {
          const formattedClaims = claimsArray.map((claim) => ({
            adjusterName: claim.adjusterName || 'N/A',
            claimNumber: claim.claimNumber || 'N/A',
            createdTimestamp: claim.createdTimestamp || new Date().toISOString(),
            currentStatus: claim.currentStatus || 'N/A',
            incident_summary: claim.incident_summary || 'N/A',
            incident_type: claim.incident_type || 'N/A',
            insuredName: claim.insuredName || 'N/A',
            locator: claim.locator || 'N/A',
            paidAmount: claim.paidAmount || '0.00',
            policyLocator: claim.policyLocator || 'N/A'
          }));
          console.log('Formatted Claims:', formattedClaims);
          setClaims(formattedClaims);
        } else {
          console.warn('No valid claims array found in response');
          setClaims([]);
        }
      } catch (parseError) {
        console.error('Error parsing response body:', parseError);
        setError('Error parsing response data. Please check the console for details.');
        setClaims([]);
      }
    } catch (err) {
      console.error('API Error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while fetching claims data');
      setClaims([]);
    } finally {
      setLoading(false);
    }
  };
  
  

  useEffect(() => {
    if (selectedDataSource) {
      handleDataSourceChange(selectedDataSource);
    }
  }, []);

  return (
    <Container>
      <SpaceBetween size="l">
        <Header
          variant="h1"
          description="View policyholders information from 3rd Party Claims Systems such as Guidewire. For the DEMO purpose, we have the API integration enabled for Guidewire. This page wont work if you don't have the Claims system (Guidewire) credentials updated as enviornment variables to `gp-fsi-claimsprocessing-3P-integration` Lambda function."
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Select
                selectedOption={selectedDataSource}
                onChange={({ detail }) => handleDataSourceChange(detail.selectedOption)}
                options={dataSourceOptions}
                placeholder="Select a data source"
                disabled={loading}
              />
              <Button
                variant="link"
                iconName="arrow-left"
                onClick={handleGoBack}
              >
                Back to Home
              </Button>
            </SpaceBetween>
          }
        >
          Guidewire - Sample Integration DEMO 
        </Header>

        {error && (
          <Box color="error" padding={{ bottom: 's' }}>
            <SpaceBetween size="xs">
              <Box variant="awsui-key-label">Error</Box>
              <div>{error}</div>
            </SpaceBetween>
          </Box>
        )}

<Table
  columnDefinitions={columnDefinitions}
  items={claims}
  loading={loading}
  loadingText={`Loading claims from ${selectedDataSource.label}`}
  header={
    <Header
      counter={claims.length > 0 ? `(${claims.length})` : undefined}
      actions={
        <Button
          onClick={() => handleDataSourceChange(selectedDataSource)}
          iconName="refresh"
          disabled={loading}
        >
          Refresh
        </Button>
      }
    >
      {`${selectedDataSource.label} Claims`}
    </Header>
  }
  empty={
    <Box textAlign="center" color="inherit" padding={{ top: 'l', bottom: 'l' }}>
      <SpaceBetween size="s">
        <b>No claims found</b>
        <Box variant="p">
          No claims data available from {selectedDataSource.label}
        </Box>
      </SpaceBetween>
    </Box>
  }
  stickyHeader
  stripedRows
  variant="full-page"
  wrapLines
  pageSize={10}
  visibleColumns={[
    'claimNumber',
    'insuredName',
    'currentStatus',
    'incident_type',
    'adjusterName',
    'paidAmount',
    'createdTimestamp',
    'policyLocator'
  ]}
/>


      </SpaceBetween>
    </Container>
  );
};

export default ClaimsIntegrationGW;
