import React, { useState } from 'react';
import type { DataQualitySummary, ForecastVintage } from '../../api/types';

interface DataQualityCardProps {
  dataQuality: DataQualitySummary | null;
  forecastVintages: ForecastVintage[];
  isLoading?: boolean;
}

export const DataQualityCard: React.FC<DataQualityCardProps> = ({
  dataQuality,
  forecastVintages,
  isLoading,
}) => {
  const [showVintages, setShowVintages] = useState(false);

  if (isLoading || !dataQuality) {
    return (
      <div className="card skeleton-container" aria-busy="true">
        <div className="skeleton-line skeleton-title" style={{ width: '30%' }} />
        <div className="skeleton-line" style={{ height: '60px' }} />
      </div>
    );
  }

  return (
    <div className="card data-quality-card" role="region" aria-label="Data Quality & Vintages">
      <div className="quality-header">
        <h3 className="quality-title">Data Quality & Pipeline Integrity</h3>
        <button
          type="button"
          className="btn btn-subtle btn-xs"
          onClick={() => setShowVintages(!showVintages)}
        >
          {showVintages ? 'Hide Forecast Vintages' : `Show Forecast Vintages (${forecastVintages.length})`}
        </button>
      </div>

      <div className="quality-stats-grid">
        <div className="stat-item">
          <span className="stat-label">Expected Grid</span>
          <span className="stat-value tabular">{dataQuality.n_expected} h</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Matched Periods</span>
          <span className="stat-value tabular text-pos">{dataQuality.n_matched} h</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Missing Forecast</span>
          <span className="stat-value tabular">{dataQuality.n_missing_forecast} h</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Missing Actual</span>
          <span className="stat-value tabular">{dataQuality.n_missing_actual} h</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Duplicate Actuals</span>
          <span className="stat-value tabular">{dataQuality.duplicate_actual_rows}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Duplicate Forecasts</span>
          <span className="stat-value tabular">{dataQuality.duplicate_forecast_rows}</span>
        </div>
      </div>

      {dataQuality.warnings && dataQuality.warnings.length > 0 && (
        <div className="quality-warnings-list">
          {dataQuality.warnings.map((w, idx) => (
            <div key={idx} className="warning-item">
              <span aria-hidden="true">⚠️</span> {w}
            </div>
          ))}
        </div>
      )}

      {showVintages && (
        <div className="vintages-panel">
          <h4 className="vintages-title">Selected Forecast Vintages (Runs used under active cutoff)</h4>
          <div className="vintages-list">
            {forecastVintages.map((v) => (
              <div key={v.publish_time} className="vintage-row">
                <span className="vintage-time tabular">
                  {v.publish_time.replace('T', ' ').replace('Z', ' UTC')}
                </span>
                <span className="badge badge-neutral tabular">
                  {v.periods_count} period{v.periods_count !== 1 ? 's' : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

