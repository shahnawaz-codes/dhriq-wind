import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  fetchMeta,
  fetchSummary,
  ApiClientError,
  buildQueryString,
} from '../api/client';

describe('buildQueryString', () => {
  it('correctly formats defined params and drops empty or null values', () => {
    const qs = buildQueryString({
      start_date: '2026-01-01',
      cutoff_time: '09:00',
      empty: '',
      nullVal: null,
      undefVal: undefined,
      page: 1,
    });
    expect(qs).toBe('?start_date=2026-01-01&cutoff_time=09%3A00&page=1');
  });

  it('returns empty string if all params are omitted', () => {
    expect(buildQueryString({})).toBe('');
  });
});

describe('ApiClient', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('maps 400 Bad Request to ApiClientError with code and details', async () => {
    const mockErrorBody = {
      error: {
        code: 'INVALID_PARAMETER',
        message: 'Invalid cutoff time format',
        details: [{ field: 'cutoff_time' }],
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => mockErrorBody,
    } as unknown as Response);

    try {
      await fetchSummary({ cutoff_time: '99:99' });
      expect.fail('Should have thrown an ApiClientError');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiClientError);
      const apiErr = err as ApiClientError;
      expect(apiErr.status).toBe(400);
      expect(apiErr.code).toBe('INVALID_PARAMETER');
      expect(apiErr.message).toBe('Invalid cutoff time format');
      expect(apiErr.details).toEqual([{ field: 'cutoff_time' }]);
    }
  });

  it('fetches successfully on 200 OK', async () => {
    const mockSuccess = {
      window: { start_date: '2026-01-01', end_date: '2026-01-31', expected_periods: 744 },
      assumptions: {
        cutoff_time_default: '09:00',
        cutoff_timezone: 'Europe/London',
        cutoff_rule: 'latest_published_at_or_before',
        cutoff_inclusive: true,
        status: 'provisional_assumption',
      },
      provenance: {
        source: 'Elexon Insights API',
        datasets: ['FUELHH', 'WINDFOR'],
        fetched_at: '2026-01-31T23:00:00Z',
        cache_age_seconds: 120,
        stale: false,
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockSuccess,
    } as unknown as Response);

    const result = await fetchMeta();
    expect(result.window.expected_periods).toBe(744);
    expect(result.provenance.stale).toBe(false);
  });
});
