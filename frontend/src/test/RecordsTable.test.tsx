import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RecordsTable } from '../components/dashboard/RecordsTable';
import type { RecordsResponse } from '../api/types';

describe('RecordsTable', () => {
  const mockRecordsData: RecordsResponse = {
    page: 1,
    page_size: 25,
    total_items: 2,
    total_pages: 1,
    items: [
      {
        start_time: '2026-01-01T00:00:00Z',
        delivery_date: '2026-01-01',
        cutoff_time: '09:00',
        actual_mw: 9500.5,
        forecast_mw: 11000.0,
        forecast_publish_time: '2025-12-31T08:45:00Z',
        forecast_horizon_hours: 15.25,
        error_mw: -1499.5,
        abs_error_mw: 1499.5,
        status: 'matched',
      },
      {
        start_time: '2026-01-01T01:00:00Z',
        delivery_date: '2026-01-01',
        cutoff_time: '09:00',
        actual_mw: null,
        forecast_mw: null,
        forecast_publish_time: null,
        forecast_horizon_hours: null,
        error_mw: null,
        abs_error_mw: null,
        status: 'missing_both',
      },
    ],
  };

  it('renders records table with correct data, formats, and status chips', () => {
    const handleFilterChange = vi.fn();
    render(
      <RecordsTable
        recordsData={mockRecordsData}
        statusFilter=""
        minAbsError=""
        sortBy="start_time"
        sortDir="asc"
        page={1}
        pageSize={25}
        onFilterChange={handleFilterChange}
      />
    );

    // Verify item 1
    expect(screen.getByText('9,500.5')).toBeInTheDocument();
    expect(screen.getByText('11,000.0')).toBeInTheDocument();
    expect(screen.getByText('-1,499.5')).toBeInTheDocument();
    expect(screen.getByText('Matched')).toBeInTheDocument();

    // Verify item 2 (missing values render as "—")
    const missingBoth = screen.getAllByText('Missing Both');
    expect(missingBoth.length).toBeGreaterThan(0);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });

  it('calls onFilterChange when column header is clicked for sorting', () => {
    const handleFilterChange = vi.fn();
    render(
      <RecordsTable
        recordsData={mockRecordsData}
        statusFilter=""
        minAbsError=""
        sortBy="start_time"
        sortDir="asc"
        page={1}
        pageSize={25}
        onFilterChange={handleFilterChange}
      />
    );

    // Click on |Error| (MW) sort button
    const absErrorSortBtn = screen.getByRole('button', { name: /\|Error\| \(MW\)/i });
    fireEvent.click(absErrorSortBtn);

    expect(handleFilterChange).toHaveBeenCalledWith({
      sortBy: 'abs_error_mw',
      sortDir: 'asc',
      page: 1,
    });
  });

  it('toggles sort direction when active sort column header is clicked', () => {
    const handleFilterChange = vi.fn();
    render(
      <RecordsTable
        recordsData={mockRecordsData}
        statusFilter=""
        minAbsError=""
        sortBy="start_time"
        sortDir="asc"
        page={1}
        pageSize={25}
        onFilterChange={handleFilterChange}
      />
    );

    // Click start time header (already active asc)
    const timeSortBtn = screen.getByRole('button', { name: /Start Time \(UTC\)/i });
    fireEvent.click(timeSortBtn);

    expect(handleFilterChange).toHaveBeenCalledWith({
      sortDir: 'desc',
      page: 1,
    });
  });

  it('renders aria-sort attributes correctly', () => {
    const handleFilterChange = vi.fn();
    const { container } = render(
      <RecordsTable
        recordsData={mockRecordsData}
        statusFilter=""
        minAbsError=""
        sortBy="start_time"
        sortDir="asc"
        page={1}
        pageSize={25}
        onFilterChange={handleFilterChange}
      />
    );

    const sortedTh = container.querySelector('th[aria-sort="ascending"]');
    expect(sortedTh).toBeInTheDocument();
  });
});
