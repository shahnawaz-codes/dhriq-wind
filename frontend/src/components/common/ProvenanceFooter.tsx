import React from 'react';
import type { ProvenanceMeta } from '../../api/types';

interface ProvenanceFooterProps {
  provenance: ProvenanceMeta | null;
}

export const ProvenanceFooter: React.FC<ProvenanceFooterProps> = ({ provenance }) => {
  const formatFetchedAt = (iso: string | null) => {
    if (!iso) return 'Not yet fetched';
    return iso.replace('T', ' ').replace('Z', ' UTC');
  };

  const formatCacheAge = (seconds: number | null) => {
    if (seconds === null || seconds === undefined) return '—';
    if (seconds < 60) return `${seconds}s ago`;
    const mins = Math.floor(seconds / 60);
    return `${mins}m ago`;
  };

  return (
    <footer className="app-footer" role="contentinfo">
      {provenance?.stale && (
        <div className="stale-cache-alert card" role="alert">
          <strong>⚠️ Stale Data Warning:</strong> Elexon upstream API was unreachable during the latest refresh cycle. Displaying cached data from {formatFetchedAt(provenance.fetched_at)}.
        </div>
      )}

      <div className="footer-inner">
        <div className="footer-metadata">
          <div className="footer-item">
            <span className="footer-label">Upstream Source:</span>
            <span>{provenance?.source || 'Elexon Insights API'}</span>
          </div>
          <div className="footer-item">
            <span className="footer-label">Datasets:</span>
            <span>{provenance?.datasets?.join(', ') || 'FUELHH, WINDFOR'}</span>
          </div>
          <div className="footer-item">
            <span className="footer-label">Fetched At:</span>
            <span className="tabular">{formatFetchedAt(provenance?.fetched_at || null)}</span>
          </div>
          <div className="footer-item">
            <span className="footer-label">Cache Age:</span>
            <span className="tabular">{formatCacheAge(provenance?.cache_age_seconds ?? null)}</span>
          </div>
        </div>

        <div className="footer-attribution">
          <p>
            Contains BMRS data © Elexon Limited copyright and/or database right 2026.
          </p>
          <p className="footer-disclaimer">
            Evaluation performed for UK Day-Ahead electricity procurement benchmarking.
          </p>
        </div>
      </div>
    </footer>
  );
};

