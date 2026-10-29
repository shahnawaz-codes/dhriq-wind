import React, { useState } from 'react';

export interface KpiCardProps {
  label: string;
  value: string | number | null;
  unit?: string;
  secondaryText?: string;
  badge?: {
    text: string;
    variant: 'neutral' | 'warning' | 'danger' | 'success';
  };
  tooltip?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  unit,
  secondaryText,
  badge,
  tooltip,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const displayValue =
    value === null || value === undefined
      ? '—'
      : typeof value === 'number'
      ? value.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })
      : value;

  return (
    <div className="card kpi-card" tabIndex={0}>
      <div className="kpi-header">
        <span className="kpi-label">{label}</span>
        <div className="kpi-tooltip-wrapper">
          <button
            type="button"
            className="tooltip-trigger"
            aria-label={`About ${label}`}
            onClick={() => setShowTooltip(!showTooltip)}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            onFocus={() => setShowTooltip(true)}
            onBlur={() => setShowTooltip(false)}
          >
            ⓘ
          </button>
          {showTooltip && (
            <div className="tooltip-popover" role="tooltip">
              {tooltip}
            </div>
          )}
        </div>
      </div>

      <div className="kpi-body">
        <div className="kpi-value-row">
          <span className="kpi-value tabular">{displayValue}</span>
          {unit && displayValue !== '—' && <span className="kpi-unit">{unit}</span>}
        </div>

        <div className="kpi-footer-row">
          {badge && (
            <span className={`badge badge-${badge.variant}`}>{badge.text}</span>
          )}
          {secondaryText && <span className="kpi-secondary">{secondaryText}</span>}
        </div>
      </div>
    </div>
  );
};

