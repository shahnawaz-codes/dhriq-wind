import React from 'react';

interface HeaderProps {
  onOpenMethodology: () => void;
  isStale?: boolean;
  isLoading?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenMethodology,
  isStale = false,
  isLoading = false,
}) => {
  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="header-branding">
          <div className="title-row">
            <h1>UK Wind Forecast Accuracy</h1>
            <span className="badge badge-neutral">January 2026</span>
            {isStale ? (
              <span className="badge badge-warning" title="Serving cached data due to upstream connectivity">
                ● Stale Cache
              </span>
            ) : isLoading ? (
              <span className="badge badge-neutral" title="Refreshing data from Elexon API">
                ◌ Refreshing...
              </span>
            ) : (
              <span className="badge badge-success" title="Live connection to Elexon BMRS API">
                ● Live Data
              </span>
            )}
          </div>
          <p className="header-description">
            Evaluating day-ahead national wind generation forecasts against actual metered outturn to inform procurement risk buffers.
          </p>
        </div>

        <div className="header-actions">
          <button
            type="button"
            className="btn btn-subtle"
            onClick={onOpenMethodology}
            aria-label="View evaluation methodology and business rules"
          >
            <span aria-hidden="true">📖</span> Methodology & Rules
          </button>
        </div>
      </div>
    </header>
  );
};

