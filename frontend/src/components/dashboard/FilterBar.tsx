import React, { useState } from 'react';

interface FilterBarProps {
  startDate: string;
  endDate: string;
  cutoffTime: string;
  granularity: 'hourly' | 'daily';
  minDate?: string;
  maxDate?: string;
  defaultCutoff?: string;
  isRecalculating?: boolean;
  onFilterChange: (filters: {
    startDate: string;
    endDate: string;
    cutoffTime: string;
    granularity: 'hourly' | 'daily';
  }) => void;
}

const COMMON_CUTOFFS = [
  { value: '06:00', label: '06:00 (Early Morning)' },
  { value: '09:00', label: '09:00 (Default Provisional)' },
  { value: '12:00', label: '12:00 (Midday)' },
  { value: '15:00', label: '15:00 (Afternoon)' },
  { value: '18:00', label: '18:00 (Evening)' },
  { value: '22:00', label: '22:00 (Night)' },
  { value: 'custom', label: 'Custom Time...' },
];

export const FilterBar: React.FC<FilterBarProps> = ({
  startDate,
  endDate,
  cutoffTime,
  granularity,
  minDate = '2026-01-01',
  maxDate = '2026-01-31',
  defaultCutoff = '09:00',
  isRecalculating = false,
  onFilterChange,
}) => {
  const [localStart, setLocalStart] = useState(startDate);
  const [localEnd, setLocalEnd] = useState(endDate);
  const [localCutoff, setLocalCutoff] = useState(cutoffTime);
  const [cutoffMode, setCutoffMode] = useState<string>(
    COMMON_CUTOFFS.some((c) => c.value === cutoffTime) ? cutoffTime : 'custom'
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  const isDefaultState =
    localStart === minDate &&
    localEnd === maxDate &&
    localCutoff === defaultCutoff;

  const validateAndApply = (newStart: string, newEnd: string, newCutoff: string, newGran: 'hourly' | 'daily') => {
    if (newStart > newEnd) {
      setValidationError('Start date cannot be after end date.');
      return;
    }
    if (newStart < minDate || newEnd > maxDate) {
      setValidationError(`Dates must be within ${minDate} to ${maxDate}.`);
      return;
    }
    setValidationError(null);
    onFilterChange({
      startDate: newStart,
      endDate: newEnd,
      cutoffTime: newCutoff,
      granularity: newGran,
    });
  };

  const handleCutoffSelectChange = (val: string) => {
    setCutoffMode(val);
    if (val !== 'custom') {
      setLocalCutoff(val);
      validateAndApply(localStart, localEnd, val, granularity);
    }
  };

  const handleCustomCutoffBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const val = e.target.value.trim();
    if (/^([01]\d|2[0-3]):[0-5]\d$/.test(val)) {
      setLocalCutoff(val);
      validateAndApply(localStart, localEnd, val, granularity);
    } else {
      setValidationError('Cutoff time must be in HH:MM format (00:00 to 23:59).');
    }
  };

  const handlePresetWeek = (start: string, end: string) => {
    setLocalStart(start);
    setLocalEnd(end);
    validateAndApply(start, end, localCutoff, granularity);
  };

  const handleReset = () => {
    setLocalStart(minDate);
    setLocalEnd(maxDate);
    setLocalCutoff(defaultCutoff);
    setCutoffMode(defaultCutoff);
    setValidationError(null);
    onFilterChange({
      startDate: minDate,
      endDate: maxDate,
      cutoffTime: defaultCutoff,
      granularity,
    });
  };

  return (
    <div className="card filter-bar-card" role="region" aria-label="Evaluation Filters">
      <div className="filter-controls-grid">
        {/* Date Range */}
        <div className="filter-group">
          <label htmlFor="filter-start-date" className="filter-label">
            Start Date
          </label>
          <input
            id="filter-start-date"
            type="date"
            className="filter-input"
            min={minDate}
            max={maxDate}
            value={localStart}
            onChange={(e) => {
              setLocalStart(e.target.value);
              validateAndApply(e.target.value, localEnd, localCutoff, granularity);
            }}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="filter-end-date" className="filter-label">
            End Date
          </label>
          <input
            id="filter-end-date"
            type="date"
            className="filter-input"
            min={minDate}
            max={maxDate}
            value={localEnd}
            onChange={(e) => {
              setLocalEnd(e.target.value);
              validateAndApply(localStart, e.target.value, localCutoff, granularity);
            }}
          />
        </div>

        {/* Cutoff Selector (P0) */}
        <div className="filter-group cutoff-group">
          <div className="label-with-badge">
            <label htmlFor="filter-cutoff-select" className="filter-label">
              Decision Cutoff (D−1)
            </label>
            <span className="badge badge-warning" title="Cutoff is provisional">
              P0 Selector
            </span>
          </div>

          <div className="cutoff-inputs-row">
            <select
              id="filter-cutoff-select"
              className="filter-select"
              value={cutoffMode}
              onChange={(e) => handleCutoffSelectChange(e.target.value)}
              aria-label="Select decision cutoff time preset"
            >
              {COMMON_CUTOFFS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>

            {cutoffMode === 'custom' && (
              <input
                id="filter-custom-cutoff"
                type="time"
                className="filter-input custom-cutoff-input"
                defaultValue={localCutoff}
                onBlur={handleCustomCutoffBlur}
                aria-label="Custom cutoff time in HH:MM"
              />
            )}
          </div>
        </div>

        {/* Granularity Toggle */}
        <div className="filter-group">
          <label className="filter-label">Granularity</label>
          <div className="segmented-control" role="radiogroup" aria-label="View Granularity">
            <button
              type="button"
              className={`seg-btn ${granularity === 'hourly' ? 'active' : ''}`}
              role="radio"
              aria-checked={granularity === 'hourly'}
              onClick={() => {
                validateAndApply(localStart, localEnd, localCutoff, 'hourly');
              }}
            >
              Hourly
            </button>
            <button
              type="button"
              className={`seg-btn ${granularity === 'daily' ? 'active' : ''}`}
              role="radio"
              aria-checked={granularity === 'daily'}
              onClick={() => {
                validateAndApply(localStart, localEnd, localCutoff, 'daily');
              }}
            >
              Daily
            </button>
          </div>
        </div>
      </div>

      {validationError && (
        <div className="filter-error-row" role="alert">
          <span aria-hidden="true">⚠️</span> {validationError}
        </div>
      )}

      {/* Preset Quick Actions & Reset Row */}
      <div className="filter-presets-row">
        <div className="presets-group">
          <span className="preset-label">Quick Presets:</span>
          <button
            type="button"
            className="btn btn-subtle btn-xs"
            onClick={() => handlePresetWeek('2026-01-01', '2026-01-31')}
          >
            Full Month
          </button>
          <button
            type="button"
            className="btn btn-subtle btn-xs"
            onClick={() => handlePresetWeek('2026-01-01', '2026-01-07')}
          >
            W1 (Jan 1–7)
          </button>
          <button
            type="button"
            className="btn btn-subtle btn-xs"
            onClick={() => handlePresetWeek('2026-01-08', '2026-01-14')}
          >
            W2 (Jan 8–14)
          </button>
          <button
            type="button"
            className="btn btn-subtle btn-xs"
            onClick={() => handlePresetWeek('2026-01-15', '2026-01-21')}
          >
            W3 (Jan 15–21)
          </button>
          <button
            type="button"
            className="btn btn-subtle btn-xs"
            onClick={() => handlePresetWeek('2026-01-22', '2026-01-28')}
          >
            W4 (Jan 22–28)
          </button>
        </div>

        <div className="filter-status-actions">
          {isRecalculating && (
            <span className="recalculating-indicator" aria-live="polite">
              ◌ Recalculating metrics...
            </span>
          )}

          {!isDefaultState && (
            <button
              type="button"
              className="btn btn-subtle btn-xs reset-btn"
              onClick={handleReset}
            >
              ↺ Reset to default
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

