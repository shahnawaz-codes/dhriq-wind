import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterBar } from '../components/dashboard/FilterBar';

describe('FilterBar', () => {
  it('renders with initial values', () => {
    const handleFilterChange = vi.fn();
    render(
      <FilterBar
        startDate="2026-01-01"
        endDate="2026-01-31"
        cutoffTime="09:00"
        granularity="hourly"
        onFilterChange={handleFilterChange}
      />
    );

    expect(screen.getByLabelText(/^Start Date/i)).toHaveValue('2026-01-01');
    expect(screen.getByLabelText(/^End Date/i)).toHaveValue('2026-01-31');
    expect(screen.getByLabelText(/Decision Cutoff \(D−1\)/i)).toHaveValue('09:00');
  });

  it('validates start date cannot be after end date', () => {
    const handleFilterChange = vi.fn();
    render(
      <FilterBar
        startDate="2026-01-01"
        endDate="2026-01-31"
        cutoffTime="09:00"
        granularity="hourly"
        onFilterChange={handleFilterChange}
      />
    );

    const startInput = screen.getByLabelText(/^Start Date/i);

    // Set start date to 2026-02-01 (after end date 2026-01-31)
    fireEvent.change(startInput, { target: { value: '2026-02-05' } });

    expect(screen.getByText(/Start date cannot be after end date/i)).toBeInTheDocument();
    expect(handleFilterChange).not.toHaveBeenCalled();
  });

  it('calls onFilterChange when valid cutoff is selected', () => {
    const handleFilterChange = vi.fn();
    render(
      <FilterBar
        startDate="2026-01-01"
        endDate="2026-01-31"
        cutoffTime="09:00"
        granularity="hourly"
        onFilterChange={handleFilterChange}
      />
    );

    const cutoffSelect = screen.getByLabelText(/Decision Cutoff \(D−1\)/i);

    // Select 12:00
    fireEvent.change(cutoffSelect, { target: { value: '12:00' } });

    expect(handleFilterChange).toHaveBeenCalledWith({
      startDate: '2026-01-01',
      endDate: '2026-01-31',
      cutoffTime: '12:00',
      granularity: 'hourly',
    });
  });

  it('switches granularity between hourly and daily', () => {
    const handleFilterChange = vi.fn();
    render(
      <FilterBar
        startDate="2026-01-01"
        endDate="2026-01-31"
        cutoffTime="09:00"
        granularity="hourly"
        onFilterChange={handleFilterChange}
      />
    );

    const dailyBtn = screen.getByRole('radio', { name: /Daily/i });
    fireEvent.click(dailyBtn);

    expect(handleFilterChange).toHaveBeenCalledWith({
      startDate: '2026-01-01',
      endDate: '2026-01-31',
      cutoffTime: '09:00',
      granularity: 'daily',
    });
  });
});
