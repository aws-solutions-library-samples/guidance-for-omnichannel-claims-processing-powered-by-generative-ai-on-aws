import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand } from '@aws-sdk/lib-dynamodb';
import { getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';
import {
  Alert,
  Box,
  Button,
  Container,
  FormField,
  Header,
  Input,
  SpaceBetween,
  FileUpload,
  StatusIndicator
} from '@cloudscape-design/components';

const AWS_REGION = process.env.REACT_APP_AWS_REGION || '';
const REACT_APP_DDBTableNameClaim = process.env.REACT_APP_DDBTableNameClaim || '';
const REACT_APP_S3BUCKET = process.env.REACT_APP_S3BUCKET || '';

interface UploadStatus {
  status: 'success' | 'error' | 'loading';
  message: string;
}

const DocUpload = () => {
  const navigate = useNavigate();
  const [caseNumber, setCaseNumber] = useState('');
  const [caseValidated, setCaseValidated] = useState(false);
  const [caseValidating, setCaseValidating] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [driverLicense, setDriverLicense] = useState<File | null>(null);
  const [accidentImages, setAccidentImages] = useState<File[]>([]);
  const [uploadStatus, setUploadStatus] = useState<Record<number, UploadStatus>>({});
  const [licenseUploadStatus, setLicenseUploadStatus] = useState<UploadStatus | null>(null);
  const [isUploading, setIsUploading] = useState(false);

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
      const ddbClient = new DynamoDBClient(clientConfig);
      const docClient = DynamoDBDocumentClient.from(ddbClient);

      return { s3Client, docClient };
    } catch (error) {
      console.error('Error initializing AWS clients:', error);
      setErrorMessage('Failed to initialize AWS services');
      throw error;
    }
  };

  const handleGoBack = () => {
    navigate('/');
  };

  const validateCaseNumber = async () => {
    try {
      setCaseValidating(true);
      setErrorMessage('');

      if (!caseNumber) {
        setErrorMessage('Please enter a case number');
        return;
      }

      const { docClient } = await initializeAWSClients();

      const command = new GetCommand({
        TableName: REACT_APP_DDBTableNameClaim,
        Key: {
          CaseNumber: caseNumber
        }
      });

      const response = await docClient.send(command);

      if (!response.Item) {
        setErrorMessage('Case number not found. Please check and try again.');
        return;
      }

      setCaseValidated(true);

    } catch (error) {
      console.error('Error validating case number:', error);
      setErrorMessage(
        error instanceof Error 
          ? `Error validating case number: ${error.message}` 
          : 'Error validating case number. Please try again.'
      );
    } finally {
      setCaseValidating(false);
    }
  };

  const handleLicenseUpload = ({ detail: { value } }: { detail: { value: File[] } }) => {
    if (value.length > 0) {
      setDriverLicense(value[0]);
    }
  };

  const removeLicense = () => {
    setDriverLicense(null);
    setLicenseUploadStatus(null);
  };

  const uploadLicenseToS3 = async () => {
    if (!driverLicense) return;

    try {
      setIsUploading(true);
      const { s3Client } = await initializeAWSClients();
      
      const licenseKey = `upload/${caseNumber}/license-${driverLicense.name}`;
      const fileBuffer = await driverLicense.arrayBuffer();
      
      const command = new PutObjectCommand({
        Bucket: REACT_APP_S3BUCKET,
        Key: licenseKey,
        Body: new Uint8Array(fileBuffer),
        ContentType: driverLicense.type
      });
  
      await s3Client.send(command);
      setLicenseUploadStatus({ status: 'success', message: 'License uploaded successfully' });
    } catch (error) {
      console.error('License upload error:', error);
      setLicenseUploadStatus({ status: 'error', message: 'License upload failed' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleImageUpload = ({ detail: { value } }: { detail: { value: File[] } }) => {
    if (accidentImages.length + value.length > 5) {
      setErrorMessage('Maximum 5 images allowed');
      return;
    }
    setAccidentImages([...accidentImages, ...value]);
  };

  const removeImage = (index: number) => {
    setAccidentImages(accidentImages.filter((_, i) => i !== index));
    const newUploadStatus = { ...uploadStatus };
    delete newUploadStatus[index];
    setUploadStatus(newUploadStatus);
  };

  const uploadVehicleImagesToS3 = async () => {
    try {
      setIsUploading(true);
      const { s3Client } = await initializeAWSClients();

      for (let i = accidentImages.length - 1; i >= 0; i--) {
        const file = accidentImages[i];
        const fileNumber = accidentImages.length - i;
        
        try {
          const fileBuffer = await file.arrayBuffer();
          
          const vehicleKey = `upload/${caseNumber}/vehicle${fileNumber}-${file.name}`;
          const command = new PutObjectCommand({
            Bucket: REACT_APP_S3BUCKET,
            Key: vehicleKey,
            Body: new Uint8Array(fileBuffer),
            ContentType: file.type
          });
  
          await s3Client.send(command);
          setUploadStatus(prev => ({
            ...prev,
            [i]: { status: 'success', message: 'Uploaded successfully' }
          }));

          // Add delay between uploads
          if (i > 0) {
            await new Promise(resolve => setTimeout(resolve, 6000));
          }
        } catch (error) {
          console.error(`Error uploading image ${i}:`, error);
          setUploadStatus(prev => ({
            ...prev,
            [i]: { status: 'error', message: 'Upload failed' }
          }));
        }
      }
    } catch (error) {
      console.error('Vehicle images upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Container>
      <SpaceBetween size="l">
        <Header 
          variant="h1" 
          info={null}
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
          Document Upload
        </Header>

        {/* Case Number Validation Section */}
        <Box margin={{ bottom: 'l' }}>
          <SpaceBetween size="m">
            <FormField
              label="Case Number"
              description="Use an existing Case Number. If you dont have one, use the 'Initiate Claim' tab to create a case."
              errorText={errorMessage}
            >
              <SpaceBetween direction="horizontal" size="xs">
                <Input
                  value={caseNumber}
                  onChange={({ detail }) => setCaseNumber(detail.value)}
                  disabled={caseValidated}
                />
                <Button
                  onClick={validateCaseNumber}
                  loading={caseValidating}
                  disabled={caseValidated}
                >
                  Validate Case
                </Button>
                {caseValidated && (
                  <Button
                    onClick={() => {
                      setCaseValidated(false);
                      setCaseNumber('');
                      setErrorMessage('');
                      setDriverLicense(null);
                      setAccidentImages([]);
                      setUploadStatus({});
                      setLicenseUploadStatus(null);
                    }}
                  >
                    Change Case
                  </Button>
                )}
              </SpaceBetween>
            </FormField>
          </SpaceBetween>
        </Box>

        {caseValidated && (
          <>
            {/* Driver's License Upload Section */}
            <Box margin={{ bottom: 'l' }}>
              <SpaceBetween size="m">
                <FormField
                  label="Upload Driver's License"
                  description="Upload a copy of your driver's license (JPG, PNG)"
                  constraintText="Required document"
                >
                  <FileUpload
                    onChange={handleLicenseUpload}
                    value={driverLicense ? [driverLicense] : []}
                    accept="image/*"
                    multiple={false}
                    constraintText="Only one file allowed"
                    i18nStrings={{
                      dropzone: "Drop driver's license here or choose file",
                      button: "Choose file"
                    }}
                  />
                </FormField>

                {/* Display uploaded license */}
                {driverLicense && (
                  <Box padding="s">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <img
                          src={URL.createObjectURL(driverLicense)}
                          alt="License Preview"
                          style={{ width: '50px', height: '50px', objectFit: 'cover' }}
                        />
                        <span>{driverLicense.name}</span>
                        {licenseUploadStatus && (
                          <StatusIndicator type={licenseUploadStatus.status}>
                            {licenseUploadStatus.message}
                          </StatusIndicator>
                        )}
                      </div>
                      <SpaceBetween direction="horizontal" size="xs">
                        <Button onClick={removeLicense}>Remove</Button>
                        <Button
                          variant="primary"
                          onClick={uploadLicenseToS3}
                          loading={isUploading}
                          disabled={isUploading || !driverLicense}
                        >
                          Upload License
                        </Button>
                      </SpaceBetween>
                    </div>
                  </Box>
                )}
              </SpaceBetween>
            </Box>

            {/* Vehicle Images Upload Section */}
            <Box margin={{ bottom: 'l' }}>
              <SpaceBetween size="m">
                <FormField
                  label="Upload Vehicle Images"
                  description="Upload up to 5 images related to the vehicle damage (JPG, PNG)"
                  constraintText="Maximum 5 images allowed"
                >
                  <FileUpload
                    onChange={handleImageUpload}
                    value={[]}
                    accept="image/*"
                    multiple
                    constraintText={`${accidentImages.length}/5 images uploaded`}
                    i18nStrings={{
                      dropzone: "Drop images here or choose files",
                      button: "Choose files"
                    }}
                  />
                </FormField>

                {/* Display uploaded images */}
                {accidentImages.length > 0 && (
                  <Box padding="s">
                    <SpaceBetween size="m">
                      {accidentImages.map((file, index) => (
                        <div key={index} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <img
                              src={URL.createObjectURL(file)}
                              alt={`Preview ${index + 1}`}
                              style={{ width: '50px', height: '50px', objectFit: 'cover' }}
                            />
                            <span>{file.name}</span>
                            {uploadStatus[index] && (
                              <StatusIndicator type={uploadStatus[index].status}>
                                {uploadStatus[index].message}
                              </StatusIndicator>
                            )}
                          </div>
                          <Button onClick={() => removeImage(index)}>Remove</Button>
                        </div>
                      ))}
                    </SpaceBetween>

                    <Box margin={{ top: 'l' }}>
                      <Button
                        variant="primary"
                        onClick={uploadVehicleImagesToS3}
                        loading={isUploading}
                        disabled={isUploading || accidentImages.length === 0}
                      >
                        Upload Vehicle Images
                      </Button>
                    </Box>
                  </Box>
                )}
              </SpaceBetween>
            </Box>
          </>
        )}
      </SpaceBetween>
    </Container>
  );
};

export default DocUpload;
