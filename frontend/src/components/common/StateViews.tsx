import React from 'react';

interface ErrorStateProps {
  message: string;
  code?: string;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, code, onRetry }) => {
  return (
    <div className="card state-card error-card" role="alert">
      <div className="state-icon error-icon" aria-hidden="true">
        ⚠️
      </div>
      <h3 className="state-title">Unable to Load Forecast Data</h3>
      <p className="state-message">{message}</p>
      {code && <span className="badge badge-danger">Code: {code}</span>}
      <div className="state-actions">
        <button type="button" className="btn btn-primary" onClick={onRetry}>
          ↻ Retry Request
        </button>
      </div>
    </div>
  );
};

interface EmptyStateProps {
  title?: string;
  message?: string;
  onReset?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Evaluation Data Found',
  message = 'There are no matched periods for the selected dates and decision cutoff. Try adjusting your date range or selecting a later cutoff.',
  onReset,
}) => {
  return (
    <div className="card state-card empty-card" role="region" aria-label="No data">
      <div className="state-icon empty-icon" aria-hidden="true">
        🔍
      </div>
      <h3 className="state-title">{title}</h3>
      <p className="state-message">{message}</p>
      {onReset && (
        <div className="state-actions">
          <button type="button" className="btn btn-subtle" onClick={onReset}>
            ↺ Reset to Full January Window
          </button>
        </div>
      )}
    </div>
  );
};

