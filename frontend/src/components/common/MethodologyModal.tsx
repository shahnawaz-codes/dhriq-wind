import React, { useEffect, useRef } from 'react';

interface MethodologyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MethodologyModal: React.FC<MethodologyModalProps> = ({ isOpen, onClose }) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      // Focus modal
      modalRef.current?.focus();
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="methodology-title"
    >
      <div
        className="modal-container card"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
        ref={modalRef}
      >
        <div className="modal-header">
          <h2 id="methodology-title">Evaluation Methodology & Business Rules</h2>
          <button
            type="button"
            className="btn btn-subtle close-btn"
            onClick={onClose}
            aria-label="Close methodology modal"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <section className="method-section">
            <h3>1. Decision Cutoff & Forecast Vintage Selection</h3>
            <p>
              To evaluate day-ahead procurement accuracy without future data leakage, only forecasts published at or before the decision cutoff on the day prior to delivery ($D - 1$) are eligible:
            </p>
            <code>publishTime ≤ (delivery_date - 1 day) at cutoff_time (Europe/London)</code>
            <p>
              The <strong>latest eligible publication</strong> before the cutoff is selected. If no forecast was published on or before the cutoff, the period is classified as <code>missing_forecast</code>. No fallback to late forecasts is permitted.
            </p>
            <div className="callout callout-warning">
              <strong>Provisional Cutoff Notice:</strong> The default cutoff time of <code>09:00 Europe/London</code> on $D - 1$ is an illustrative evaluation benchmark, <em>not</em> an established statutory gate closure. You can use the cutoff selector in the filter bar to evaluate accuracy across different trading decision horizons (e.g. 06:00, 12:00, 18:00).
            </div>
          </section>

          <section className="method-section">
            <h3>2. Hourly Grid & Strict :30 Exclusion</h3>
            <p>
              The evaluation grid for January 2026 consists strictly of <strong>744 top-of-hour UTC instants</strong> (<code>2026-01-01T00:00:00Z</code> to <code>2026-01-31T23:00:00Z</code>, 31 days × 24 hours).
            </p>
            <p>
              While raw Elexon <code>FUELHH</code> provides actual generation every 30 minutes (:00 and :30), the national wind forecast (<code>WINDFOR</code>) is published natively on hourly intervals (:00). To avoid unverified mathematical assumptions (such as synthetic interpolation or persistence), <strong>FUELHH :30 actuals are strictly excluded from all error metrics and evaluation denominators</strong>.
            </p>
          </section>

          <section className="method-section">
            <h3>3. Accuracy Metric Formulas</h3>
            <p>For each matched period i = 1 to n:</p>
            <ul>
              <li><strong>Error (e):</strong> Actual − Forecast (MW).</li>
              <li><strong>Absolute Error (|e|):</strong> |Actual − Forecast| (MW).</li>
              <li><strong>Mean Absolute Error (MAE):</strong> (1 / n) × Σ |e| (MW). Measures the average magnitude of the forecast miss.</li>
              <li><strong>Root Mean Squared Error (RMSE):</strong> √( (1 / n) × Σ e² ) (MW). Penalises larger forecast errors more heavily.</li>
              <li>
                <strong>Mean Error / Bias:</strong> (1 / n) × Σ e (MW).
                <br />
                <span className="text-muted">Positive value = forecasts were too low on average (under-forecasting).</span>
                <br />
                <span className="text-muted">Negative value = forecasts were too high on average (over-forecasting).</span>
              </li>
              <li><strong>P90 Absolute Error:</strong> 90th percentile of |e| using linear interpolation (Method 7 / NumPy default). Useful for sizing reserve procurement buffers.</li>
              <li><strong>MAE % of Mean Actual:</strong> (MAE / Mean Actual) × 100%.</li>
              <li><strong>Data Coverage:</strong> (n_matched / 744) × 100%. Completeness across expected January periods.</li>
            </ul>
          </section>

          <section className="method-section">
            <h3>4. Missing Data & Zero Handling</h3>
            <p>
              Actual zero wind generation (valid calm conditions) is preserved. True missing periods are categorized into explicit statuses (<code>missing_forecast</code>, <code>missing_actual</code>, <code>missing_both</code>) and rendered as visual gaps on the chart—<strong>never filled with zero</strong>.
            </p>
          </section>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
