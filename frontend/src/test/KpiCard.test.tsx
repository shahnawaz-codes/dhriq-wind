import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { KpiCard } from '../components/dashboard/KpiCard';
import { KpiGrid } from '../components/dashboard/KpiGrid';

describe('KpiCard', () => {
  it('renders label, value, and unit correctly', () => {
    render(
      <KpiCard
        label="MAE"
        value={1234.56}
        unit="MW"
        secondaryText="Mean Absolute Error"
      />
    );

    expect(screen.getByText('MAE')).toBeInTheDocument();
    expect(screen.getByText('1,234.6')).toBeInTheDocument();
    expect(screen.getByText('MW')).toBeInTheDocument();
    expect(screen.getByText('Mean Absolute Error')).toBeInTheDocument();
  });

  it('renders dash "—" when value is null or undefined', () => {
    render(<KpiCard label="Bias" value={null} unit="MW" />);

    expect(screen.getByText('Bias')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('renders string values directly', () => {
    render(<KpiCard label="Matched Periods" value="744 (100.0%)" />);

    expect(screen.getByText('Matched Periods')).toBeInTheDocument();
    expect(screen.getByText('744 (100.0%)')).toBeInTheDocument();
  });

  it('shows tooltip on mouse enter or focus', () => {
    render(
      <KpiCard
        label="RMSE"
        value={1500}
        tooltip="Root Mean Squared Error explanation"
      />
    );

    const infoBtn = screen.getByRole('button', { name: /About RMSE/i });
    expect(infoBtn).toBeInTheDocument();

    // Trigger hover
    fireEvent.mouseEnter(infoBtn);
    expect(screen.getByRole('tooltip')).toHaveTextContent('Root Mean Squared Error explanation');

    // Trigger mouse leave
    fireEvent.mouseLeave(infoBtn);
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });
});

describe('KpiGrid', () => {
  it('renders all 7 key metrics and displays matched periods as both count and percentage', () => {
    const mockMetrics = {
      n_matched: 744,
      mae_mw: 2127.5,
      rmse_mw: 2750.8,
      bias_mw: -1851.5,
      mae_pct_of_mean_actual: 18.4,
      p90_abs_error_mw: 4200.0,
      mean_actual_mw: 11500.0,
      mean_forecast_mw: 13351.5,
      coverage_pct: 100.0,
    };

    const mockDataQuality = {
      n_expected: 744,
      n_matched: 744,
      n_missing_actual: 0,
      n_missing_forecast: 0,
      n_missing_both: 0,
      invalid_actual_rows: 0,
      invalid_forecast_rows: 0,
      duplicate_actual_rows: 0,
      duplicate_forecast_rows: 0,
      conflicting_forecast_rows: 0,
      warnings: [],
    };

    render(<KpiGrid metrics={mockMetrics} dataQuality={mockDataQuality} />);

    // Check Matched Periods count + percentage format
    expect(screen.getByText('744 (100.0%)')).toBeInTheDocument();

    // Check Bias badge and value
    expect(screen.getByText('-1,851.5')).toBeInTheDocument();
    expect(screen.getByText('Over-forecast')).toBeInTheDocument();

    // Check MAE, RMSE, P90
    expect(screen.getByText('2,127.5')).toBeInTheDocument();
    expect(screen.getByText('2,750.8')).toBeInTheDocument();
    expect(screen.getByText('4,200.0')).toBeInTheDocument();

    // Check Data Coverage
    expect(screen.getByText('100.0%')).toBeInTheDocument();
  });
});
