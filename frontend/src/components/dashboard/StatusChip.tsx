import React from 'react';

interface StatusChipProps {
  status: 'matched' | 'missing_forecast' | 'missing_actual' | 'missing_both' | string;
}

export const StatusChip: React.FC<StatusChipProps> = ({ status }) => {
  switch (status) {
    case 'matched':
      return (
        <span className="badge badge-success status-chip" title="Both actual and eligible forecast present">
          <span aria-hidden="true">✓</span> Matched
        </span>
      );
    case 'missing_forecast':
      return (
        <span className="badge badge-warning status-chip" title="No forecast published on or before cutoff">
          <span aria-hidden="true">∅</span> No Forecast
        </span>
      );
    case 'missing_actual':
      return (
        <span className="badge badge-danger status-chip" title="Actual generation data missing from Elexon">
          <span aria-hidden="true">✕</span> No Actual
        </span>
      );
    case 'missing_both':
      return (
        <span className="badge badge-neutral status-chip" title="Both actual and forecast missing">
          <span aria-hidden="true">?</span> Missing Both
        </span>
      );
    default:
      return <span className="badge badge-neutral status-chip">{status}</span>;
  }
};

