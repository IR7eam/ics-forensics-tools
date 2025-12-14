import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL
});

export function setAuthToken(token?: string) {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
}

export async function login(username: string, password: string) {
  const data = new URLSearchParams();
  data.append('username', username);
  data.append('password', password);
  const response = await apiClient.post('/auth/token', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  return response.data as { access_token: string; token_type: string };
}

export async function fetchAuditLogs(filters: {
  actor?: string;
  action?: string;
  resource?: string;
  status?: string;
  limit?: number;
}) {
  const response = await apiClient.get('/audit', { params: filters });
  return response.data as Array<{
    id: number;
    actor: string;
    action: string;
    resource: string;
    status: string;
    detail: Record<string, unknown>;
    timestamp: string;
  }>;
}
