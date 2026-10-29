import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  BarChart,
  Bar,
  ReferenceLine,
} from 'recharts';
import type { DailySeriesPoint, HourlySeriesPoint } from '../../api/types';

interface ForecastChartProps {
  granularity: 'hourly' | 'daily';
  points: (HourlySeriesPoint | DailySeriesPoint)[];
  cutoffTime: string;
  isLoading?: boolean;
}

function formatXAxisTick(value: string, granularity: 'hourly' | 'daily'): string {
  if (!value) return '';
  if (granularity === 'daily') {
    // Value is YYYY-MM-DD
    const parts = value.split('-');
    if (parts.length === 3) {
      return `${parts[2]} Jan`;
    }
    return value;
  }

  // Value is ISO string YYYY-MM-DDTHH:mm:ssZ
  const dt = new Date(value);
  if (isNaN(dt.getTime())) return value;
  const day = dt.getUTCDate().toString().padStart(2, '0');
  const hour = dt.getUTCHours().toString().padStart(2, '0');
  return `${day}d ${hour}:00`;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  granularity: 'hourly' | 'daily';
}

const CustomHourlyTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0 || !label) {
    return null;
  }

  const pointData = payload[0]?.payload as HourlySeriesPoint;
  const dtStr = label ? label.replace('T', ' ').replace('Z', ' UTC') : '';

  const actual = pointData.actual_mw;
  const forecast = pointData.forecast_mw;
  const error = actual !== null && forecast !== null ? actual - forecast : null;

  return (
    <div className="chart-tooltip card" role="tooltip">
      <div className="tooltip-title">{dtStr}</div>
      <div className="tooltip-grid">
        <div className="tooltip-item actual-item">
          <span className="tooltip-swatch" style={{ background: '#1B5E9E' }} />
          <span className="tooltip-label">Actual:</span>
          <span className="tooltip-val tabular">
            {actual !== null ? `${actual.toLocaleString(undefined, { minimumFractionDigits: 1 })} MW` : 'No actual data'}
          </span>
        </div>

        <div className="tooltip-item forecast-item">
          <span className="tooltip-swatch dashed-swatch" style={{ borderColor: '#C2570C' }} />
          <span className="tooltip-label">Forecast:</span>
          <span className="tooltip-val tabular">
            {forecast !== null ? `${forecast.toLocaleString(undefined, { minimumFractionDigits: 1 })} MW` : 'No eligible forecast'}
          </span>
        </div>

        {error !== null && (
          <div className="tooltip-item error-item">
            <span className="tooltip-label">Error (A − F):</span>
            <span className={`tooltip-val tabular ${error < 0 ? 'text-danger' : 'text-pos'}`}>
              {error > 0 ? `+${error.toFixed(1)}` : error.toFixed(1)} MW
            </span>
          </div>
        )}

        {pointData.forecast_publish_time && (
          <div className="tooltip-extra">
            <span className="extra-label">Vintage:</span>
            <span className="extra-val">{pointData.forecast_publish_time.replace('T', ' ').replace('Z', ' UTC')}</span>
          </div>
        )}

        {pointData.actual_half_hour_context_mw !== null && (
          <div className="tooltip-extra context-extra">
            <span className="extra-label">:30 context actual:</span>
            <span className="extra-val">{pointData.actual_half_hour_context_mw.toFixed(1)} MW (non-metric)</span>
          </div>
        )}
      </div>
    </div>
  );
};

export const ForecastChart: React.FC<ForecastChartProps> = ({
  granularity,
  points,
  cutoffTime,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="card chart-card skeleton-container" aria-busy="true">
        <div className="skeleton-line skeleton-title" style={{ width: '40%' }} />
        <div className="chart-skeleton-box" />
      </div>
    );
  }

  if (!points || points.length === 0) {
    return (
      <div className="card chart-card empty-chart">
        <p>No chart data available for the selected filters.</p>
      </div>
    );
  }

  return (
    <div className="card chart-card" role="region" aria-label="Forecast vs Actual Generation Chart">
      <div className="chart-header">
        <div>
          <h2 className="chart-title">
            {granularity === 'hourly'
              ? 'Hourly Actual vs Day-Ahead Forecast Generation (MW)'
              : 'Daily Mean Generation & Accuracy Metrics (MW)'}
          </h2>
          <p className="chart-subtitle">
            {granularity === 'hourly'
              ? `Showing top-of-hour periods (UTC). Missing data shown as line gaps. Active Cutoff: ${cutoffTime} Europe/London.`
              : `Aggregated daily outturn and day-ahead forecast accuracy metrics across January 2026.`}
          </p>
        </div>
      </div>

      <div className="chart-wrapper">
        {granularity === 'hourly' ? (
          <ResponsiveContainer width="100%" height={380}>
            <LineChart
              data={points}
              margin={{ top: 10, right: 20, left: 10, bottom: 25 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#E1E4E8" vertical={false} />
              <XAxis
                dataKey="start_time"
                tickFormatter={(val) => formatXAxisTick(val, 'hourly')}
                stroke="#52606D"
                tick={{ fontSize: 11 }}
                interval={23} /* Show tick roughly once per day */
              />
              <YAxis
                stroke="#52606D"
                tick={{ fontSize: 11 }}
                unit=" MW"
                domain={[0, 'auto']}
              />
              <Tooltip content={<CustomHourlyTooltip granularity="hourly" />} />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ paddingBottom: '10px' }}
              />
              {/* Actual generation: solid blue line */}
              <Line
                type="monotone"
                dataKey="actual_mw"
                name="Actual Wind (FUELHH)"
                stroke="#1B5E9E"
                strokeWidth={2}
                dot={false}
                connectNulls={false} /* Missing values as gaps, NEVER zeroes */
              />
              {/* Forecast generation: dashed amber line */}
              <Line
                type="monotone"
                dataKey="forecast_mw"
                name={`Day-Ahead Forecast (Cutoff ${cutoffTime})`}
                stroke="#C2570C"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                connectNulls={false} /* Missing values as gaps */
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={380}>
            <BarChart
              data={points}
              margin={{ top: 10, right: 20, left: 10, bottom: 25 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#E1E4E8" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={(val) => formatXAxisTick(val, 'daily')}
                stroke="#52606D"
                tick={{ fontSize: 11 }}
              />
              <YAxis
                stroke="#52606D"
                tick={{ fontSize: 11 }}
                unit=" MW"
              />
              <ReferenceLine y={0} stroke="#1F2933" />
              <Tooltip
                formatter={(val: any, name: any) => [
                  typeof val === 'number' ? `${val.toFixed(1)} MW` : '—',
                  name,
                ]}
                labelFormatter={(lbl) => `${lbl} (Delivery Date)`}
              />
              <Legend verticalAlign="top" align="right" wrapperStyle={{ paddingBottom: '10px' }} />
              <Bar dataKey="mae_mw" name="Daily MAE (MW)" fill="#1B5E9E" radius={[4, 4, 0, 0]} />
              <Bar dataKey="bias_mw" name="Daily Bias (MW)" fill="#C2570C" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

