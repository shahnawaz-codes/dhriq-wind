import React from 'react';
import type { RecordItem, RecordsResponse } from '../../api/types';
import { StatusChip } from './StatusChip';

interface RecordsTableProps {
  recordsData: RecordsResponse | null;
  statusFilter: string;
  minAbsError: string;
  sortBy: string;
  sortDir: 'asc' | 'desc';
  page: number;
  pageSize: number;
  isLoading?: boolean;
  onFilterChange: (filters: {
    status?: string;
    minAbsError?: string;
    sortBy?: string;
    sortDir?: 'asc' | 'desc';
    page?: number;
    pageSize?: number;
  }) => void;
}

export const RecordsTable: React.FC<RecordsTableProps> = ({
  recordsData,
  statusFilter,
  minAbsError,
  sortBy,
  sortDir,
  page,
  pageSize,
  isLoading,
  onFilterChange,
}) => {
  const handleSort = (field: string) => {
    if (sortBy === field) {
      onFilterChange({ sortDir: sortDir === 'asc' ? 'desc' : 'asc', page: 1 });
    } else {
      onFilterChange({ sortBy: field, sortDir: 'asc', page: 1 });
    }
  };

  const getAriaSort = (field: string) => {
    if (sortBy !== field) return 'none';
    return sortDir === 'asc' ? 'ascending' : 'descending';
  };

  const renderSortIcon = (field: string) => {
    if (sortBy !== field) return <span className="sort-indicator neutral">↕</span>;
    return <span className="sort-indicator active">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  const formatDateTime = (isoStr: string | null) => {
    if (!isoStr) return '—';
    // Format YYYY-MM-DD HH:mm
    return isoStr.replace('T', ' ').replace(':00Z', '').replace('Z', ' UTC');
  };

  const formatMw = (val: number | null) => {
    if (val === null || val === undefined) return '—';
    return val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  };

  const formatSignedError = (val: number | null) => {
    if (val === null || val === undefined) return '—';
    const formatted = val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    if (val > 0) return <span className="text-pos">+{formatted}</span>;
    if (val < 0) return <span className="text-danger">{formatted}</span>;
    return <span>{formatted}</span>;
  };

  const totalItems = recordsData?.total_items || 0;
  const totalPages = recordsData?.total_pages || 1;
  const startItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalItems);

  return (
    <div className="card table-card" role="region" aria-label="Comparison Records Table">
      <div className="table-toolbar">
        <div>
          <h2 className="table-title">Hourly Evaluation Records</h2>
          <p className="table-subtitle">
            Showing top-of-hour periods with actual generation and selected day-ahead forecast outturn.
          </p>
        </div>

        <div className="table-filters-row">
          {/* Status Filter */}
          <div className="filter-item">
            <label htmlFor="table-status-filter" className="filter-label-inline">
              Status:
            </label>
            <select
              id="table-status-filter"
              className="table-select"
              value={statusFilter}
              onChange={(e) => onFilterChange({ status: e.target.value, page: 1 })}
            >
              <option value="all">All Records</option>
              <option value="matched">Matched Only</option>
              <option value="missing_forecast">Missing Forecast</option>
              <option value="missing_actual">Missing Actual</option>
              <option value="missing_both">Missing Both</option>
            </select>
          </div>

          {/* Min Absolute Error Filter */}
          <div className="filter-item">
            <label htmlFor="table-min-err" className="filter-label-inline">
              Min |Error| (MW):
            </label>
            <input
              id="table-min-err"
              type="number"
              min="0"
              placeholder="e.g. 500"
              className="table-input"
              value={minAbsError}
              onChange={(e) => onFilterChange({ minAbsError: e.target.value, page: 1 })}
            />
          </div>

          {/* Page Size Select */}
          <div className="filter-item">
            <label htmlFor="table-page-size" className="filter-label-inline">
              Rows:
            </label>
            <select
              id="table-page-size"
              className="table-select"
              value={pageSize}
              onChange={(e) => onFilterChange({ pageSize: Number(e.target.value), page: 1 })}
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      </div>

      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col" aria-sort={getAriaSort('start_time')}>
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => handleSort('start_time')}
                >
                  Start Time (UTC) {renderSortIcon('start_time')}
                </button>
              </th>
              <th scope="col" aria-sort={getAriaSort('actual_mw')} className="text-right">
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => handleSort('actual_mw')}
                >
                  Actual (MW) {renderSortIcon('actual_mw')}
                </button>
              </th>
              <th scope="col" aria-sort={getAriaSort('forecast_mw')} className="text-right">
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => handleSort('forecast_mw')}
                >
                  Forecast (MW) {renderSortIcon('forecast_mw')}
                </button>
              </th>
              <th scope="col" aria-sort={getAriaSort('error_mw')} className="text-right">
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => handleSort('error_mw')}
                >
                  Error (MW) {renderSortIcon('error_mw')}
                </button>
              </th>
              <th scope="col" aria-sort={getAriaSort('abs_error_mw')} className="text-right">
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => handleSort('abs_error_mw')}
                >
                  |Error| (MW) {renderSortIcon('abs_error_mw')}
                </button>
              </th>
              <th scope="col" aria-sort={getAriaSort('forecast_publish_time')}>
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => handleSort('forecast_publish_time')}
                >
                  Selected Vintage (UTC) {renderSortIcon('forecast_publish_time')}
                </button>
              </th>
              <th scope="col" aria-sort={getAriaSort('forecast_horizon_hours')} className="text-right">
                <button
                  type="button"
                  className="table-sort-btn"
                  onClick={() => handleSort('forecast_horizon_hours')}
                >
                  Horizon (h) {renderSortIcon('forecast_horizon_hours')}
                </button>
              </th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(pageSize > 10 ? 10 : pageSize)].map((_, i) => (
                <tr key={i} className="skeleton-row">
                  <td colSpan={8}>
                    <div className="skeleton-line" style={{ height: '24px' }} />
                  </td>
                </tr>
              ))
            ) : !recordsData?.items || recordsData.items.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-table-cell">
                  No records match the current status or error criteria.
                </td>
              </tr>
            ) : (
              recordsData.items.map((row: RecordItem) => (
                <tr key={row.start_time}>
                  <td className="tabular">{formatDateTime(row.start_time)}</td>
                  <td className="text-right tabular font-medium">{formatMw(row.actual_mw)}</td>
                  <td className="text-right tabular">{formatMw(row.forecast_mw)}</td>
                  <td className="text-right tabular">{formatSignedError(row.error_mw)}</td>
                  <td className="text-right tabular">{formatMw(row.abs_error_mw)}</td>
                  <td className="tabular text-muted">{formatDateTime(row.forecast_publish_time)}</td>
                  <td className="text-right tabular text-muted">
                    {row.forecast_horizon_hours !== null ? `${row.forecast_horizon_hours.toFixed(1)} h` : '—'}
                  </td>
                  <td>
                    <StatusChip status={row.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="table-pagination">
        <div className="pagination-info">
          Showing <strong>{startItem}</strong>–<strong>{endItem}</strong> of <strong>{totalItems}</strong> records
        </div>

        <div className="pagination-controls">
          <button
            type="button"
            className="btn btn-subtle btn-sm"
            disabled={page <= 1 || isLoading}
            onClick={() => onFilterChange({ page: 1 })}
            aria-label="First page"
          >
            « First
          </button>
          <button
            type="button"
            className="btn btn-subtle btn-sm"
            disabled={page <= 1 || isLoading}
            onClick={() => onFilterChange({ page: page - 1 })}
            aria-label="Previous page"
          >
            ‹ Prev
          </button>
          <span className="pagination-current">
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            className="btn btn-subtle btn-sm"
            disabled={page >= totalPages || isLoading}
            onClick={() => onFilterChange({ page: page + 1 })}
            aria-label="Next page"
          >
            Next ›
          </button>
          <button
            type="button"
            className="btn btn-subtle btn-sm"
            disabled={page >= totalPages || isLoading}
            onClick={() => onFilterChange({ page: totalPages })}
            aria-label="Last page"
          >
            Last »
          </button>
        </div>
      </div>
    </div>
  );
};

