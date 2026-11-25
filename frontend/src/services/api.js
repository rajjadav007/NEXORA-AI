import { API_BASE_URL } from '../config/constants.js';

/**
 * Base HTTP request helper
 */
export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    let message = errorBody.message || `Request failed with status ${response.status}`;
    if (typeof errorBody.detail === 'string') {
      message = errorBody.detail;
    } else if (Array.isArray(errorBody.detail) && errorBody.detail.length > 0) {
      message = errorBody.detail.map((item) => item.msg || JSON.stringify(item)).join('; ');
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export const apiService = {
  get: (endpoint) => apiRequest(endpoint, { method: 'GET' }),
  post: (endpoint, data) => apiRequest(endpoint, { method: 'POST', body: JSON.stringify(data) }),
};
