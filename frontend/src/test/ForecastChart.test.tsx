import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ForecastChart } from '../components/dashboard/ForecastChart';
import type { HourlySeriesPoint, DailySeriesPoint } from '../api/types';

// Mock recharts responsive container for JSDOM
vi.mock('recharts', async () => {
  const original = await vi.importActual<any>('recharts');
  return {
    ...original,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container" style={{ width: 800, height: 380 }}>
        {children}
      </div>
    ),
  };
});

describe('ForecastChart', () => {
  it('renders empty message when points array is empty', () => {
    render(
      <ForecastChart
        granularity="hourly"
        points={[]}
        cutoffTime="09:00"
      />
    );

    expect(screen.getByText(/No chart data available for the selected filters/i)).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading is true', () => {
    const { container } = render(
      <ForecastChart
        granularity="hourly"
        points={[]}
        cutoffTime="09:00"
        isLoading={true}
      />
    );

    expect(container.querySelector('.skeleton-container')).toBeInTheDocument();
  });

  it('renders hourly chart title and responsive container when hourly points are provided', () => {
    const mockHourlyPoints: HourlySeriesPoint[] = [
      {
        start_time: '2026-01-01T00:00:00Z',
        actual_mw: 10000.0,
        forecast_mw: 11000.0,
        forecast_publish_time: '2025-12-31T07:30:00Z',
        status: 'matched',
        actual_half_hour_context_mw: 9800.0,
      },
      {
        start_time: '2026-01-01T01:00:00Z',
        actual_mw: null,
        forecast_mw: null,
        forecast_publish_time: null,
        status: 'missing_both',
        actual_half_hour_context_mw: null,
      },
    ];

    render(
      <ForecastChart
        granularity="hourly"
        points={mockHourlyPoints}
        cutoffTime="09:00"
      />
    );

    expect(
      screen.getByText(/Hourly Actual vs Day-Ahead Forecast Generation \(MW\)/i)
    ).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders daily chart title and container when daily points are provided', () => {
    const mockDailyPoints: DailySeriesPoint[] = [
      {
        date: '2026-01-01',
        n_matched: 24,
        mean_actual_mw: 10500.0,
        mean_forecast_mw: 11200.0,
        mae_mw: 1200.0,
        rmse_mw: 1400.0,
        bias_mw: -700.0,
        cutoff_time: '2025-12-31T09:00:00Z',
      },
    ];

    render(
      <ForecastChart
        granularity="daily"
        points={mockDailyPoints}
        cutoffTime="09:00"
      />
    );

    expect(
      screen.getByText(/Daily Mean Generation & Accuracy Metrics \(MW\)/i)
    ).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });
});

