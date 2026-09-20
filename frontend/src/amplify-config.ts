import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: 'ap-south-1_oPFT3UAsE',
      userPoolClientId: '59a7ircm7tfaommsvo5si3g21m',
      loginWith: {
        email: true,
      },
    },
  },
});
