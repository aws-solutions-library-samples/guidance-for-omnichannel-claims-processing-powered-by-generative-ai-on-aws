import React, { useState, ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { WithAuthenticatorProps } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import HomePage from './pages/HomePage.tsx';
import MainPage from './pages/MainPage.tsx';
import InitiateClaim from './pages/InitiateClaim.tsx';
import DocUpload from './pages/DocUpload.tsx';
import Adjudicate from './pages/Adjudicate.tsx';
import ClaimsIntegration from './pages/ClaimsIntegration.tsx';
import ClaimsIntegrationgw from './pages/ClaimsIntegrationgw.tsx';

import GenAIAssistant from './pages/GenAIAssistant.tsx';
import { SideNavigationProps } from "@cloudscape-design/components";
import GlobalHeader from "./components/global-header.tsx";
import { AuthWrapper } from "./components/AuthWrapper.tsx";
import {
  AppLayout,
  SideNavigation,
} from "@cloudscape-design/components";


interface ProtectedRouteProps {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  return <AuthWrapper >{children}</AuthWrapper>;
};

const AppContent = () => {
  const [navigationHidden] = useState(false);
  const [activeHref, setActiveHref] = useState('/');

  const Navigation = () => {
    const navigate = useNavigate();
  
    const handleNavigate = (e: CustomEvent<SideNavigationProps.FollowDetail>) => {
      e.preventDefault();
      const href = e.detail.href;
      
      if (href === "/Documentation") {
        window.open('https://aws.amazon.com/solutions/guidance/omnichannel-claims-processing-powered-by-generative-ai-on-aws/', '_blank');
      } else if (href === "/PartnerCentral") {
        window.open('https://partnercentral.awspartner.com/partnercentral2/s/article?category=Advanced_resources&article=Omnichannel-Claims-Processing-Powered-by-Generative-AI-on-AWS', '_blank');
      } else {
        setActiveHref(href);
        navigate(href);
      }
    };
  
    return (
      <SideNavigation
        activeHref={activeHref}
        header={{
          href: "/",
          text: "Info"
        }}
        onFollow={handleNavigate}
        items={[
          { type: "link", text: "Home", href: "/MainPage" },
          { type: "link", text: "Initiate Claim", href: "/InitiateClaim" },
          { type: "link", text: "Upload Documents", href: "/DocUpload" },
          { type: "link", text: "Adjudicate", href: "/Adjudicate" },
          { type: "link", text: "Socotra Integration", href: "/ClaimsIntegration" },
          { type: "link", text: "Guidewire Integration", href: "/ClaimsIntegrationgw" },
          { type: "link", text: "GenAIAssistant", href: "/GenAIAssistant" },
          { type: "link", text: "Documentation", href: "/Documentation" },
          { type: "link", text: "Partner Central", href: "/PartnerCentral" }
        ]}
      />
    );
  };

  return (
    <BrowserRouter>
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100vh' 
      }}>
        <div style={{ flexShrink: 0 }}>
          <GlobalHeader />
        </div>
        <div style={{ 
          flex: '1 1 auto',
          marginTop: '60px'
        }}>
          <AppLayout
            navigationHide={navigationHidden}
            navigation={<Navigation />}
            content={
              <div style={{ padding: '20px' }}>
                <Routes>
                  <Route 
                    path="/" 
                    element={
                      <ProtectedRoute>
                        <HomePage />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/MainPage" 
                    element={
                      <ProtectedRoute>
                        <MainPage />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/InitiateClaim" 
                    element={
                      <ProtectedRoute>
                        <InitiateClaim />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/DocUpload" 
                    element={
                      <ProtectedRoute>
                        <DocUpload />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/GenAIAssistant" 
                    element={
                      <ProtectedRoute>
                        <GenAIAssistant />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/ClaimsIntegration" 
                    element={
                      <ProtectedRoute>
                        <ClaimsIntegration />
                      </ProtectedRoute>
                    } 
                  />
                                    <Route 
                    path="/ClaimsIntegrationgw" 
                    element={
                      <ProtectedRoute>
                        <ClaimsIntegrationgw />
                      </ProtectedRoute>
                    } 
                  />
                  <Route 
                    path="/Adjudicate" 
                    element={
                      <ProtectedRoute>
                        <Adjudicate />
                      </ProtectedRoute>
                    } 
                  />
                </Routes>
              </div>
            }
          />
        </div>
      </div>
    </BrowserRouter>
  );
};

const App = () => {
  return (
    <AuthWrapper>
      <AppContent />
    </AuthWrapper>
  );
};

export default App;
