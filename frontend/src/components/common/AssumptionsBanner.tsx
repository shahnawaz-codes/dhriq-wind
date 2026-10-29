import React from 'react';

interface AssumptionsBannerProps {
  cutoffTime: string;
  cutoffTimezone: string;
  onOpenMethodology: () => void;
}

export const AssumptionsBanner: React.FC<AssumptionsBannerProps> = ({
  cutoffTime,
  cutoffTimezone,
  onOpenMethodology,
}) => {
  return (
    <div className="assumptions-banner" role="region" aria-label="Evaluation Assumptions">
      <div className="banner-icon" aria-hidden="true">
        ℹ️
      </div>
      <div className="banner-content">
        <div className="banner-headline">
          <strong>Provisional Evaluation Cutoff: {cutoffTime} ({cutoffTimezone}) on D−1</strong>
          <span className="badge badge-warning">Provisional Benchmark</span>
        </div>
        <p className="banner-text">
          Only WINDFOR forecasts published at or before this cutoff are eligible; the latest vintage is selected. 
          This 09:00 benchmark is an illustrative decision time, not a verified market gate-closure time. 
          Use the cutoff selector below to analyze forecast accuracy across different trading decision horizons.
        </p>
      </div>
      <div className="banner-action">
        <button
          type="button"
          className="btn btn-subtle"
          onClick={onOpenMethodology}
        >
          View Rules
        </button>
      </div>
    </div>
  );
};

