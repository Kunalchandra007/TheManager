import { fetchAuthSession } from 'aws-amplify/auth';

export async function authenticatedFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === 'true') {
    return fetch(input, init);
  }

  const session = await fetchAuthSession();
  const accessToken = session.tokens?.accessToken?.toString();

  if (!accessToken) {
    throw new Error('You are not authenticated. Please sign in first.');
  }

  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${accessToken}`);

  return fetch(input, { ...init, headers });
}