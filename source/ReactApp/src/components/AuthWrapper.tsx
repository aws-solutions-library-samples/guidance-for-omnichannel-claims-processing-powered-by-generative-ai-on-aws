import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import { View, Heading, Flex } from '@aws-amplify/ui-react';
import { signOut } from 'aws-amplify/auth';
import { useEffect } from 'react';

export const AuthWrapper = ({ children }) => {
  const manageChatWidget = (isAuthenticated: boolean) => {
    const selectors = [
      '.amazon-connect-widget',
      '#amazon-connect-chat-widget',
      'iframe[title="Customer Chat"]'
    ];
    
    selectors.forEach(selector => {
      const element = document.querySelector(selector);
      if (element) {
        element.style.display = isAuthenticated ? 'block' : 'none';
      }
    });
  };

  useEffect(() => {
    manageChatWidget(false);
  }, []);

  const handleSignOut = () => {
    // First hide the chat widget
    manageChatWidget(false);
    
    // Perform sign out
    signOut()
      .then(() => {
        // Clear any cached data or local storage if needed
        localStorage.clear();
        sessionStorage.clear();
        
        // Force a hard refresh
        document.location.replace('/');
      })
      .catch((error) => {
        console.error('Error signing out:', error);
      });
  };

  return (
    <>
      <Authenticator 
        hideSignUp={true}
        components={{
          SignIn: {
            Header: () => {
              manageChatWidget(false);
              return (
                <Flex padding="1rem">
                  <Heading level={4}>Omnichannel Claims Processing on AWS</Heading>
                </Flex>
              );
            }
          }
        }}
        signOut={handleSignOut}
      >
        {({ signOut, user }) => {
          if (!user) {
            manageChatWidget(false);
            return null;
          }
          manageChatWidget(true);
          return (
            <View>
              {children}
            </View>
          );
        }}
      </Authenticator>
    </>
  );
};
