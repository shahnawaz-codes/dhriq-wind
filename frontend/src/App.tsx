import React, { useState } from 'react';
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from '@tanstack/react-query';
import {
  fetchMeta,
  fetchSummary,
  fetchSeries,
  fetchRecords,
  ApiClientError,
} from './api/client';
import { Header } from './components/common/Header';
import { AssumptionsBanner } from './components/common/AssumptionsBanner';
import { MethodologyModal } from './components/common/MethodologyModal';
import { ProvenanceFooter } from './components/common/ProvenanceFooter';
import { ErrorState } from './components/common/StateViews';
import { FilterBar } from './components/dashboard/FilterBar';
import { KpiGrid } from './components/dashboard/KpiGrid';
import { ForecastChart } from './components/dashboard/ForecastChart';
import { RecordsTable } from './components/dashboard/RecordsTable';
import { DataQualityCard } from './components/dashboard/DataQualityCard';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
});

export const Dashboard: React.FC = () => {
  // Evaluation horizon state (default January 2026, 09:00 Europe/London)
  const [startDate, setStartDate] = useState<string>('2026-01-01');
  const [endDate, setEndDate] = useState<string>('2026-01-31');
  const [cutoffTime, setCutoffTime] = useState<string>('09:00');
  const [granularity, setGranularity] = useState<'hourly' | 'daily'>('hourly');

  // Table filtering & pagination state
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [minAbsError, setMinAbsError] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('start_time');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  // Methodology modal state
  const [isMethodologyOpen, setIsMethodologyOpen] = useState<boolean>(false);

  // Queries
  const metaQuery = useQuery({
    queryKey: ['meta'],
    queryFn: fetchMeta,
    staleTime: 5 * 60 * 1000,
  });

  const summaryQuery = useQuery({
    queryKey: ['summary', startDate, endDate, cutoffTime],
    queryFn: () =>
      fetchSummary({
        start_date: startDate,
        end_date: endDate,
        cutoff_time: cutoffTime,
      }),
  });

  const seriesQuery = useQuery({
    queryKey: ['series', startDate, endDate, cutoffTime, granularity],
    queryFn: () =>
      fetchSeries({
        start_date: startDate,
        end_date: endDate,
        cutoff_time: cutoffTime,
        granularity,
      }),
  });

  const parsedMinAbsError = minAbsError ? parseFloat(minAbsError) : undefined;
  const recordsQuery = useQuery({
    queryKey: [
      'records',
      startDate,
      endDate,
      cutoffTime,
      statusFilter,
      parsedMinAbsError,
      sortBy,
      sortDir,
      page,
      pageSize,
    ],
    queryFn: () =>
      fetchRecords({
        start_date: startDate,
        end_date: endDate,
        cutoff_time: cutoffTime,
        status: statusFilter || undefined,
        min_abs_error_mw: isNaN(parsedMinAbsError ?? NaN) ? undefined : parsedMinAbsError,
        sort_by: sortBy,
        sort_dir: sortDir,
        page,
        page_size: pageSize,
      }),
    placeholderData: (previousData, previousQuery) => {
      // Keep previous data for smooth pagination/sorting, but clear on cutoff or date range changes
      const prevKey = previousQuery?.queryKey;
      if (
        prevKey &&
        prevKey[1] === startDate &&
        prevKey[2] === endDate &&
        prevKey[3] === cutoffTime
      ) {
        return previousData;
      }
      return undefined;
    },
  });

  // Filter change handler for top bar
  const handleFilterChange = (filters: {
    startDate: string;
    endDate: string;
    cutoffTime: string;
    granularity: 'hourly' | 'daily';
  }) => {
    setStartDate(filters.startDate);
    setEndDate(filters.endDate);
    setCutoffTime(filters.cutoffTime);
    setGranularity(filters.granularity);
    // Reset table page on cutoff/date changes
    setPage(1);
  };

  // Table filter/sort/pagination handler
  const handleTableFilterChange = (filters: {
    status?: string;
    minAbsError?: string;
    sortBy?: string;
    sortDir?: 'asc' | 'desc';
    page?: number;
    pageSize?: number;
  }) => {
    if (filters.status !== undefined) setStatusFilter(filters.status);
    if (filters.minAbsError !== undefined) setMinAbsError(filters.minAbsError);
    if (filters.sortBy !== undefined) setSortBy(filters.sortBy);
    if (filters.sortDir !== undefined) setSortDir(filters.sortDir);
    if (filters.page !== undefined) setPage(filters.page);
    if (filters.pageSize !== undefined) setPageSize(filters.pageSize);
  };

  // Derived state
  const isStale =
    Boolean(summaryQuery.data?.provenance?.stale) ||
    Boolean(metaQuery.data?.provenance?.stale);

  const isRecalculating =
    summaryQuery.isFetching || seriesQuery.isFetching || recordsQuery.isFetching;

  const provenance =
    summaryQuery.data?.provenance ||
    metaQuery.data?.provenance ||
    null;

  const hasFatalError = summaryQuery.isError && seriesQuery.isError;
  const errorObj = summaryQuery.error || seriesQuery.error;
  const errorMessage =
    errorObj instanceof ApiClientError
      ? errorObj.message
      : errorObj instanceof Error
      ? errorObj.message
      : 'An unexpected error occurred while communicating with the server.';
  const errorCode = errorObj instanceof ApiClientError ? errorObj.code : undefined;

  const handleRetryAll = () => {
    summaryQuery.refetch();
    seriesQuery.refetch();
    recordsQuery.refetch();
    metaQuery.refetch();
  };

  return (
    <div className="app-container">
      {/* Accessibility Skip Link */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Main Header */}
      <Header
        onOpenMethodology={() => setIsMethodologyOpen(true)}
        isStale={isStale}
        isLoading={isRecalculating}
      />

      <main id="main-content" className="main-content" tabIndex={-1}>
        {/* Provisional Cutoff Notice */}
        <AssumptionsBanner
          cutoffTime={cutoffTime}
          cutoffTimezone="Europe/London"
          onOpenMethodology={() => setIsMethodologyOpen(true)}
        />

        {/* Evaluation Controls & Cutoff Selector */}
        <FilterBar
          startDate={startDate}
          endDate={endDate}
          cutoffTime={cutoffTime}
          granularity={granularity}
          minDate="2026-01-01"
          maxDate="2026-01-31"
          defaultCutoff="09:00"
          isRecalculating={isRecalculating}
          onFilterChange={handleFilterChange}
        />

        {hasFatalError ? (
          <ErrorState
            message={errorMessage}
            code={errorCode}
            onRetry={handleRetryAll}
          />
        ) : (
          <>
            {/* KPI Metrics Grid */}
            <KpiGrid
              metrics={summaryQuery.data?.metrics ?? null}
              dataQuality={summaryQuery.data?.data_quality ?? null}
              isLoading={summaryQuery.isFetching}
            />

            {/* Time Series Chart */}
            <ForecastChart
              granularity={granularity}
              points={seriesQuery.data?.points ?? []}
              cutoffTime={cutoffTime}
              isLoading={seriesQuery.isFetching}
            />

            {/* Detailed Evaluation Records Table */}
            <RecordsTable
              recordsData={recordsQuery.data ?? null}
              statusFilter={statusFilter}
              minAbsError={minAbsError}
              sortBy={sortBy}
              sortDir={sortDir}
              page={page}
              pageSize={pageSize}
              isLoading={recordsQuery.isFetching}
              onFilterChange={handleTableFilterChange}
            />

            {/* Data Pipeline Quality & Forecast Vintages */}
            <DataQualityCard
              dataQuality={summaryQuery.data?.data_quality ?? null}
              forecastVintages={summaryQuery.data?.forecast_vintages ?? []}
              isLoading={summaryQuery.isFetching}
            />
          </>
        )}
      </main>

      {/* Data Provenance Footer */}
      <ProvenanceFooter provenance={provenance} />

      {/* Methodology & Business Rules Modal */}
      <MethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}
