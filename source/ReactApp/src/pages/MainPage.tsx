import React, { useState,useEffect } from 'react';
import {
  ContentLayout,
  Container,
  Header,
  SpaceBetween,
  Tabs,
  Table,
  Box,
  Cards,
  Badge,
  ColumnLayout,
} from "@cloudscape-design/components";
import './MainPage.css';

const REACT_APP_STRIPE_PUBLISH_KEY = process.env.REACT_APP_STRIPE_PUBLISH_KEY || '';

const MainPage = () => {
  const [activeTabId, setActiveTabId] = useState("Policies");

  useEffect(() => {
      // Create script element for Amazon Connect initialization
      const script = document.createElement('script');
      script.type = 'text/javascript';
      script.text = `
        

  (function(w, d, x, id){
    s=d.createElement('script');
    s.src='https://db08fjupg2abb.cloudfront.net/amazon-connect-chat-interface-client.js';
    s.async=1;
    s.id=id;
    d.getElementsByTagName('head')[0].appendChild(s);
    w[x] =  w[x] || function() { (w[x].ac = w[x].ac || []).push(arguments) };
  })(window, document, 'amazon_connect', 'bcdc07dd-6310-4812-b3fa-873e97db609e');
  amazon_connect('styles', { iconType: 'CHAT_VOICE', openChat: { color: '#ffffff', backgroundColor: '#123456' }, closeChat: { color: '#ffffff', backgroundColor: '#123456'} });
  amazon_connect('snippetId', 'QVFJREFIZ2ZYaENvQWJCb1ZtYmxRNlFMNVJYMlhab3BKY1p0RnRGQ2pJNGhxdnBvemdId2VnUWg1WUxabUlRWURoQmFzQVRHQUFBQWJqQnNCZ2txaGtpRzl3MEJCd2FnWHpCZEFnRUFNRmdHQ1NxR1NJYjNEUUVIQVRBZUJnbGdoa2dCWlFNRUFTNHdFUVFNcVVydkFrVUxQQkkwZUE0d0FnRVFnQ3ZFZ2ZNaEd0MVZJZXo5MFhIZFY3WmVVNjR4VkZMU3ZXaFNFK3gySE1qTEQyK2ZKS3Z3T2dNU0laWFA6OlFBZ2NaUlNWb3NxUUp3dmhhNnZEVFl1bDJma0ZlKzJuUG1SY29OOGxCWFh3WVJDU283R0xCeEJJc0VRcUIvOVQ1bkFoTUYzZXVIQWtQcmVndW5qMGpLNC9HSUhXaHB1RkhhWmt3TDA1bU1lTklxVGsrNWFsS0JBSXZycG5sUk8xdHcrRWxFMDNiQ2s2bUlmdURrWWlodHpyT1ZJZ3VzUT0=');
  amazon_connect('supportedMessagingContentTypes', [ 'text/plain', 'text/markdown', 'application/vnd.amazonaws.connect.message.interactive', 'application/vnd.amazonaws.connect.message.interactive.response' ]);

        `;
  
      // Add the script to document head
      document.head.appendChild(script);

      const script1 = document.createElement('script');
      script1.src = 'https://js.stripe.com/v3/buy-button.js';
      script1.async = true;
      document.body.appendChild(script1);
  

  
      // Cleanup function
      return () => {
        try {
          const scriptElement = document.getElementById('bcdc07dd-6310-4812-b3fa-873e97db609e');
          if (scriptElement) {
            document.head.removeChild(scriptElement);
          }
        } catch (error) {
          console.error('Error during cleanup:', error);
        }
      };
    }, []);

    
  

  return (
    <ContentLayout
      header={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Header
            variant="h1"
            className="welcome-header"
            description="Your trusted insurance partner"
            info={null}
          >
            Welcome to Anycompany Portal
          </Header>
        </div>
      }
    >
      <Container className="custom-Policies">
        <SpaceBetween size="l">
          <Tabs
            activeTabId={activeTabId}
            onChange={({ detail }) => {
              setActiveTabId(detail.activeTabId);
            }}
            tabs={[
              {
                id: "Policies",
                label: "Policies",
                content: (
                  <Container>
                    <SpaceBetween size="l">
                      <Header 
                        variant="h2"
                        className="welcome-header"
                        description="Your Insurance Policy Overview"
                        info={null}
                      >
                        Welcome, Fname LName
                      </Header>
                      <Container className="policy-container">
                        <SpaceBetween size="m">
                          <div className="policy-details">
                            <h3>Policy Details:</h3>
                            <SpaceBetween size="s">
                              <div>
                                <strong>Policy Number:</strong> PY1234
                              </div>
                              <div>
                                <strong>Coverage:</strong> Bodily Injury Liability, Property Damage Liability, Uninsured/Underinsured motorist, Comprehensive, Collision, Medical Payments, Personal Injury Protection
                              </div>
                              <div>
                                <strong>Deductible:</strong> <span className="amount-text">$500</span>
                              </div>
                              <div>
                                <strong>Premium:</strong> <span className="amount-text">$750 for 6 months</span>
                              </div>
                              <div>
                                <strong>Vehicles:</strong> Toyota Camry 2021 (VIN: 1HGCM82633A123456), Toyota Camry 2021 (1HGCM82633A654321)
                              </div>
                              <div>
                                <strong>Expiration Date:</strong> 07/31/2025
                              </div>
                            </SpaceBetween>
                          </div>
                        </SpaceBetween>
                      </Container>
                    </SpaceBetween>
                  </Container>
                )
              },
              {
                id: "claims",
                label: "Claims",
                content: (
                  <Container>
                    <SpaceBetween size="l">
                      <Header 
                        variant="h2"
                        className="welcome-header"
                        description="View your insurance claims"
                      >
                        Claims History
                      </Header>
                      <Table
                        className="claims-table"
                        columnDefinitions={[
                          {
                            id: "claimId",
                            header: "Claim ID",
                            cell: item => item.claimId
                          },
                          {
                            id: "date",
                            header: "Date Filed",
                            cell: item => item.date
                          },
                          {
                            id: "type",
                            header: "Type",
                            cell: item => item.type
                          },
                          {
                            id: "status",
                            header: "Status",
                            cell: item => (
                              <div className={`status-${item.status.toLowerCase()}`}>
                                {item.status}
                              </div>
                            )
                          },
                          {
                            id: "amount",
                            header: "Amount",
                            cell: item => <span className="amount-text">{item.amount}</span>
                          }
                        ]}
                        items={[
                          {
                            claimId: "PY1234-895363",
                            date: "01/15/2024",
                            type: "Collision Repair",
                            status: "Closed",
                            amount: "$2,800"
                          },
                          {
                            claimId: "PY1234-397482",
                            date: "02/28/2024",
                            type: "Windshield Replacement",
                            status: "Closed",
                            amount: "$650"
                          },
                          {
                            claimId: "PY1234-046223",
                            date: "03/10/2024",
                            type: "Theft Recovery",
                            status: "Closed",
                            amount: "$1,200"
                          }
                        ]}
                      />
                    </SpaceBetween>
                  </Container>
                )
              },
              {
                id: "Billing",
                label: "Billing",
                content: (
                  <Container>
                    <SpaceBetween size="l">
                      <Header 
                        variant="h2"
                        className="welcome-header"
                        description="View your payment history and upcoming payments. The link below connects you to the Stripe payment page. This is a test set up, **DO NOT MAKE ANY PAYMENTS**."
                      >
                        Payment Information
                      </Header>
                        <script async
                            src="https://js.stripe.com/v3/buy-button.js">
                          </script>

                          <stripe-buy-button
                            buy-button-id="buy_btn_1QlvYCRRei52UUPP9PftJxGr"
                            publishable-key={`${REACT_APP_STRIPE_PUBLISH_KEY}`}
                          >
                          </stripe-buy-button>
                      <Cards
                        className="payment-card"
                        cardDefinition={{
                          header: item => (
                            <Header variant="h3" className="payment-header">{item.type}</Header>
                          ),
                          sections: [
                            {
                              id: "details",
                              content: item => (
                                <SpaceBetween size="s">
                                  <div><strong>Amount:</strong> <span className="amount-text">{item.amount}</span></div>
                                  <div><strong>Due Date:</strong> {item.dueDate}</div>
                                  <div><strong>Status:</strong> {item.status}</div>
                                  {item.autopay && (
                                    <div><Badge className="custom-badge">AutoPay Enabled</Badge></div>
                                  )}
                                </SpaceBetween>
                              )
                            }
                          ]
                        }}
                        items={[
                          {
                            type: "Monthly Premium",
                            amount: "$125.00",
                            dueDate: "04/01/2025",
                            status: "Upcoming",
                            autopay: true
                          },
                          {
                            type: "Last Payment",
                            amount: "$125.00",
                            dueDate: "02/01/2025",
                            status: "Paid",
                            autopay: true
                          }
                        ]}
                      />
                      <Box className="info-box">
                        <SpaceBetween size="s">
                          <div><strong>Payment Method:</strong> Visa ending in 4321</div>
                          <div><strong>Billing Address:</strong> 123 Main St, Anytown, ST 12345</div>
                        </SpaceBetween>
                      </Box>
                    </SpaceBetween>
                  </Container>
                )
              },
              {
                id: "profile",
                label: "Profile",
                content: (
                  <Container className="profile-section">
                    <SpaceBetween size="l">
                      <Header 
                        variant="h2"
                        className="profile-header"
                        description="View your personal information"
                      >
                        Profile Details
                      </Header>
                      <ColumnLayout columns={1}>
                        <SpaceBetween size="m">
                          <Container header={<Header variant="h3">Policyholder Information</Header>}>
                            <SpaceBetween size="s">
                              <div><strong>Name:</strong> Fname LName</div>
                              <div><strong>Date of Birth:</strong> 05/15/1985</div>
                              <div><strong>Driver's License:</strong> DL123456789</div>
                              <div><strong>Email:</strong> Fname.LName@email.com</div>
                              <div><strong>Phone:</strong> (555) 123-4567</div>
                            </SpaceBetween>
                          </Container>
                        </SpaceBetween>
                        <SpaceBetween size="m">
                          <Container header={<Header variant="h3">Address</Header>}>
                            <SpaceBetween size="s">
                              <div><strong>Street:</strong> 123 Main St</div>
                              <div><strong>Apt:</strong> </div>
                              <div><strong>City:</strong> Anytown</div>
                              <div><strong>State:</strong> ST</div>
                              <div><strong>ZIP Code:</strong> 12345</div>
                            </SpaceBetween>
                          </Container>
                          <Container header={<Header variant="h3">Preferences</Header>}>
                            <SpaceBetween size="s">
                              <div><strong>Communication:</strong> Email</div>
                              <div><strong>Donot disturb:</strong> NA</div>
                              <div><strong>Paperless Billing:</strong> Enabled</div>
                              <div><strong>AutoPay:</strong> Enabled</div>
                              <div><strong>Language:</strong> English</div>
                            </SpaceBetween>
                          </Container>
                        </SpaceBetween>
                      </ColumnLayout>
                    </SpaceBetween>
                  </Container>
                )
              }
            ]}
          />
        </SpaceBetween>
      </Container>
    </ContentLayout>
  );
};

export default MainPage;
