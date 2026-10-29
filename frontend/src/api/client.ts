import type {
  ApiErrorResponse,
  MetaResponse,
  RecordsResponse,
  SeriesResponse,
  SummaryResponse,
} from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class ApiClientError extends Error {
  code: string;
  details: { field?: string }[];
  status: number;

  constructor(message: string, code = 'API_ERROR', status = 500, details: { field?: string }[] = []) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}, max503Retries = 10): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  let attempt = 0;

  while (attempt <= max503Retries) {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
        ...options,
      });

      if (response.ok) {
        return (await response.json()) as T;
      }

      // Handle 503 DATA_NOT_READY auto-retry
      if (response.status === 503 && attempt < max503Retries) {
        const retryAfterHeader = response.headers.get('Retry-After');
        const delaySeconds = retryAfterHeader ? parseInt(retryAfterHeader, 10) || 5 : 5;
        attempt++;
        await new Promise((resolve) => setTimeout(resolve, delaySeconds * 1000));
        continue;
      }

      // Parse error JSON
      let errorData: ApiErrorResponse | null = null;
      try {
        errorData = await response.json();
      } catch {
        // Response wasn't JSON
      }

      const message = errorData?.error?.message || `HTTP ${response.status}: ${response.statusText}`;
      const code = errorData?.error?.code || 'HTTP_ERROR';
      const details = errorData?.error?.details || [];

      throw new ApiClientError(message, code, response.status, details);
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        throw err;
      }
      const message = err instanceof Error ? err.message : 'Network request failed';
      throw new ApiClientError(message, 'NETWORK_ERROR', 0, []);
    }
  }

  throw new ApiClientError('Server data is not ready yet. Please try again.', 'TIMEOUT', 503);
}

export function buildQueryString(params: Record<string, string | number | undefined | null>): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value));
    }
  }
  const str = searchParams.toString();
  return str ? `?${str}` : '';
}

export async function fetchMeta(): Promise<MetaResponse> {
  return request<MetaResponse>('/api/meta');
}

export async function fetchSummary(params: {
  start_date?: string;
  end_date?: string;
  cutoff_time?: string;
}): Promise<SummaryResponse> {
  const qs = buildQueryString(params);
  return request<SummaryResponse>(`/api/summary${qs}`);
}

export async function fetchSeries(params: {
  start_date?: string;
  end_date?: string;
  cutoff_time?: string;
  granularity?: 'hourly' | 'daily';
}): Promise<SeriesResponse> {
  const qs = buildQueryString(params);
  return request<SeriesResponse>(`/api/series${qs}`);
}

export async function fetchRecords(params: {
  start_date?: string;
  end_date?: string;
  cutoff_time?: string;
  status?: string;
  min_abs_error_mw?: number;
  sort_by?: string;
  sort_dir?: string;
  page?: number;
  page_size?: number;
}): Promise<RecordsResponse> {
  const qs = buildQueryString(params);
  return request<RecordsResponse>(`/api/records${qs}`);
}

