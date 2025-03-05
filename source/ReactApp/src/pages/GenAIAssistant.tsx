import { Amplify } from 'aws-amplify';
import { fetchAuthSession } from '@aws-amplify/auth';
import { getCurrentUser } from '@aws-amplify/auth';
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthenticator } from '@aws-amplify/ui-react';
import {
  Container,
  Select,
  FormField,
  SpaceBetween,
  Button,
  TextContent,
  Header,
  Alert,
  Spinner,
  Cards,
  Box,
  Textarea
} from '@cloudscape-design/components';
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { 
  DynamoDBDocumentClient, 
  ScanCommand,
} from "@aws-sdk/lib-dynamodb";
import axios from 'axios';

const REACT_APP_REACTAPI = process.env.REACT_APP_REACTAPI || '';
const AWS_REGION = process.env.REACT_APP_AWS_REGION || '';

interface SelectOption {
  label: string;
  value: string;
}

interface ApiResponse {
  statusCode: number;
  body: string;
}

const AdjusterAssistant: React.FC = () => {
  const navigate = useNavigate();
  const { user, authStatus } = useAuthenticator((context) => [
    context.user,
    context.authStatus
  ]);

  const [models, setModels] = useState<SelectOption[]>([]);
  const [selectedModel, setSelectedModel] = useState<SelectOption | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [authLoading, setAuthLoading] = useState<boolean>(true);

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

  const fetchData = async () => {
    try {
      const { docClient } = await initializeAWSClients();

      const command = new ScanCommand({
        TableName: process.env.REACT_APP_DDBTableNameFM || 'GP-FSI-ClaimsProcessing-FM',
        ProjectionExpression: 'id, Active'
      });

      const response = await docClient.send(command);
      
      if (response.Items) {
        const modelOptions = response.Items.map(item => ({
          label: item.Active,
          value: item.Active
        }));
        setModels(modelOptions);
      }
    } catch (err) {
      console.error('Error fetching models:', err);
      setError('Failed to fetch models');
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

  
  const handleSubmit = async () => {
    if (!selectedModel) return;
    
    setLoading(true);
    setError('');
  
    try {
        const response = await fetch(REACT_APP_REACTAPI, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'Y',
                query: searchQuery
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const data = await response.json();
        
  
        // Extract the actual response content from the body
      let displayContent;
      if (typeof data === 'object' && data.data && data.data.body) {
          // Access the body through data.data.body
          displayContent = data.data.body;
      } else {
          displayContent = data;
      }

        setResponse(displayContent);
    } catch (err) {
        console.error('Error details:', err);
        setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
        setLoading(false);
    }
};


  
  const handleError = (error: any) => {
    console.error('Error:', error);
    if (error.message) {
      setError(error.message);
    } else {
      setError('An unexpected error occurred');
    }
  };

  if (authLoading) {
    return (
      <Box textAlign="center" padding={{ top: 'xxl' }}>
        <Spinner size="large" />
      </Box>
    );
  }

  return (
    <Container>
      <SpaceBetween size="l" direction="vertical">
        {[  // Wrap children in an array and map through them
          <Header
            key="header"
            variant="h1"
            description="Get AI-powered assistance for claims processing"
          >
            Generative AI Adjuster Assistant
          </Header>,

          error && (
            <Alert 
              key="error-alert"
              type="error" 
              dismissible 
              onDismiss={() => setError('')}
            >
              {error}
            </Alert>
          ),

          <FormField 
            key="model-select"
            label="Select Model"
            description="If you select the model option 'Y', as per the sample data loaded to 'GP-FSI-ClaimsProcessing-FM' DynamoDB table, it will select amazon-nova-pro"
          >
            <Select
              selectedOption={selectedModel}
              onChange={({ detail }) => 
                setSelectedModel(detail.selectedOption as SelectOption)
              }
              options={models}
              placeholder="Choose a model"
              selectedAriaLabel="Selected"
            />
          </FormField>,

          <FormField 
            key="question-input"
            label="Enter your question"
          >
            <Textarea
              value={searchQuery}
              onChange={({ detail }) => setSearchQuery(detail.value)}
              placeholder="Type your question here...eg: What is the Average Collision Repair cost"
              rows={4}
            />
          </FormField>,

          <Button
            key="submit-button"
            variant="primary"
            onClick={handleSubmit}
            disabled={loading || !selectedModel || !searchQuery}
            loading={loading}
          >
            Submit Query
          </Button>,

          loading && (
            <Box 
              key="loading-spinner"
              textAlign="center"
            >
              <Spinner size="large" />
            </Box>
          ),

          response && (
            <Box
            padding="l"
            style={{
                width: '100%',
                maxWidth: '1200px',
                margin: '0 auto'
            }}
        >
            <Cards
                key="response-cards"
                cardDefinition={{
                    header: () => (
                        <TextContent>
                            <h2>Agent Assistance Response</h2>
                        </TextContent>
                    ),
                    sections: [
                        {
                            id: "response",
                            content: () => (
                                <TextContent>
                                    <Box
                                        padding="l"
                                        style={{
                                            minHeight: '400px',
                                            maxHeight: '600px',
                                            overflowY: 'auto',
                                            backgroundColor: '#f8f8f8',  // Light background
                                            borderRadius: '4px',         // Rounded corners
                                            border: '1px solid #eee'     // Light border
                                        }}
                                    >
                                        <div style={{
                                            fontSize: '14px',
                                            lineHeight: '1.5',
                                            whiteSpace: 'pre-wrap',
                                            padding: '16px'
                                        }}>
                                            {typeof response === 'string' 
                                                ? response 
                                                : typeof response === 'object'
                                                    ? JSON.stringify(response, null, 2)
                                                    : String(response)
                                            }
                                        </div>
                                    </Box>
                                </TextContent>
                            )
                        }
                    ]
                }}
                items={[{ id: "response" }]}
                trackBy="id"
                empty={
                    <Box textAlign="center" color="inherit">
                        <b>No response yet</b>
                        <Box padding={{ bottom: "s" }}>
                            Submit a query to see the response
                        </Box>
                    </Box>
                }
            />
        </Box>
          )
        ].filter(Boolean)} {/* Filter out any null/undefined elements */}
      </SpaceBetween>
    </Container>
);

};

export default AdjusterAssistant;
