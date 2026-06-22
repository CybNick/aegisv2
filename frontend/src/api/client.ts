import type { ApiResponse, ApiError } from '../types/api';

const API_BASE = '/api/v1';

class ApiClientError extends Error {
  public code: string;
  public details: any;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiClientError';
    this.code = error.error_code;
    this.details = error.details;
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const apiKey = localStorage.getItem('aegis_api_key') || '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options?.headers as Record<string, string>,
  };
  if (apiKey) {
    headers['X-AEGIS-API-KEY'] = apiKey;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    // Attempt to parse standard error envelope
    try {
      const errorData = await response.json() as ApiError;
      throw new ApiClientError(errorData);
    } catch (e) {
      if (e instanceof ApiClientError) throw e;
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }
  }

  const data = await response.json() as ApiResponse<T>;
  if (!data.success) {
    // In M6, 200 OK could theoretically wrap a success:false if not careful, though usually 400/500
    throw new ApiClientError(data as unknown as ApiError);
  }

  return data.data;
}

export const api = {
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<T>(endpoint + qs, { method: 'GET' });
  },

  async post<T>(endpoint: string, body?: any, params?: Record<string, string>): Promise<T> {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<T>(endpoint + qs, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  async delete<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<T>(endpoint + qs, { method: 'DELETE' });
  }
};
