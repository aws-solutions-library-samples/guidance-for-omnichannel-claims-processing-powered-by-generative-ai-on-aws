import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App.tsx';
import { Amplify } from 'aws-amplify';

const awsRegion = process.env.REACT_APP_AWS_REGION;
const userPoolId = process.env.REACT_APP_COGNITO_USER_POOL_ID;
const userPoolClientId = process.env.REACT_APP_COGNITO_CLIENT_ID;
const REACT_APP_IDENTITY_POOL_ID = process.env.REACT_APP_IDENTITY_POOL_ID;
const REACT_APP_REACTAPI = process.env.REACT_APP_REACTAPI;

if (!awsRegion || !userPoolId || !userPoolClientId) {
  throw new Error('Required environment variables are not set');
}

Amplify.configure({
  Auth: {
      Cognito: {
          region: awsRegion,
          userPoolId: userPoolId,
          userPoolClientId: userPoolClientId,
          identityPoolId:REACT_APP_IDENTITY_POOL_ID,
      }
  },
  API: {
      endpoints: [
          {
              name: 'MyAPI',
              endpoint: REACT_APP_REACTAPI,
              region: awsRegion
          }
      ]
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
