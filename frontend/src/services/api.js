import axios from 'axios';
import { API_BASE_URL, GOOGLE_AUTH_API_BASE_URL } from '../config';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Normalize API errors without inventing fake success responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isNetworkError =
      !error.response &&
      (error.code === 'ERR_NETWORK' ||
        error.code === 'ECONNABORTED' ||
        error.message?.toLowerCase().includes('network'));

    const status = error.response?.status ?? null;
    const isEndpointMissing = status === 404 || status === 501 || status === 502 || status === 503;

    const normalizedError = {
      message:
        error.response?.data?.detail ||
        error.response?.data?.message ||
        (isNetworkError
          ? `Unable to reach FastAPI backend at ${error.config?.baseURL || API_BASE_URL}.`
          : error.message || 'An unexpected API error occurred.'),
      status,
      isNetworkError,
      isEndpointMissing,
      isBackendUnavailable: isNetworkError || isEndpointMissing,
      raw: error,
    };

    return Promise.reject(normalizedError);
  }
);

export async function analyzeProfile(form, file, onUploadProgress) {
  const formData = new FormData();
  formData.append('name', form.name);
  formData.append('target_role', form.target_role);
  formData.append('intensity_mode', form.intensity_mode);
  formData.append('github_username', form.github_username || '');
  formData.append('codeforces_handle', form.codeforces_handle || '');
  formData.append('leetcode_username', form.leetcode_username || '');
  formData.append('gfg_handle', form.gfg_handle || '');
  formData.append('codechef_handle', form.codechef_handle || '');
  formData.append('atcoder_handle', form.atcoder_handle || '');
  formData.append('hackerrank_handle', form.hackerrank_handle || '');
  if (file) formData.append('resume', file);

  const { data } = await apiClient.post('/api/profile/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000,
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percent);
      }
    },
  });
  return data;
}

export async function authenticateWithGoogle(credential) {
  const { data } = await apiClient.post(
    '/api/auth/google',
    { credential },
    { baseURL: GOOGLE_AUTH_API_BASE_URL }
  );
  if (!data?.access_token || !data?.user) {
    throw new Error('Google verification did not return a valid session.');
  }
  return data;
}

function requireIntegerId(id, fieldName) {
  const parsedId = Number(id);
  if (!Number.isSafeInteger(parsedId)) {
    throw new Error(`${fieldName} must be a numeric ID returned by the API.`);
  }
  return parsedId;
}

export async function getMatchedJobs(userId) {
  const id = requireIntegerId(userId, 'user_id');
  const { data } = await apiClient.get(`/api/jobs/match/${id}`, { timeout: 60000 });
  return data;
}

export async function findPod(userId) {
  const id = requireIntegerId(userId, 'user_id');
  const { data } = await apiClient.post(`/api/match/find/${id}`);
  return data;
}

export async function verifySprintProof(proof) {
  const { data } = await apiClient.post('/api/sprint/verify', proof, { timeout: 60000 });
  return data;
}

export async function simulateMidnight(partnershipId, forceMiss = true) {
  const id = requireIntegerId(partnershipId, 'partnership_id');
  const { data } = await apiClient.post(
    `/api/sprint/simulate-midnight/${id}`,
    null,
    { params: { force_miss: forceMiss } }
  );
  return data;
}

export async function generateSprintRoadmap(payload) {
  const { data } = await apiClient.post('/api/roadmap/generate', payload, { timeout: 60000 });
  return data;
}
