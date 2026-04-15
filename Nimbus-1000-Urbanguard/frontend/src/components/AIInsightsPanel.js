import React from 'react';
import './AIInsightsPanel.css';

/**
 * AIInsightsPanel Component
 * Displays AI classification insights, daily report summary,
 * and classification confidence distribution
 * 
 * Props:
 * - dailyReport: Daily report object from /daily-report
 * - complaints: Array of complaints (to extract confidence data)
 * - loading: Boolean loading state
 * - error: Error message string
 */
const AIInsightsPanel = ({ dailyReport = null, complaints = [], loading = false, error = null, classificationEngine = null }) => {

  // Calculate confidence distribution from complaints
  const getConfidenceStats = () => {
    if (!complaints || complaints.length === 0) {
      return { avg: 0, high: 0, medium: 0, low: 0, total: 0, distribution: [] };
    }

    const confidences = complaints
      .filter(c => c.classification_confidence !== undefined)
      .map(c => c.classification_confidence);

    if (confidences.length === 0) {
      return { avg: 0, high: 0, medium: 0, low: 0, total: 0, distribution: [] };
    }

    const avg = confidences.reduce((sum, c) => sum + c, 0) / confidences.length;
    const high = confidences.filter(c => c >= 0.8).length;
    const medium = confidences.filter(c => c >= 0.5 && c < 0.8).length;
    const low = confidences.filter(c => c < 0.5).length;

    // Create a simple histogram (5 buckets)
    const buckets = [0, 0, 0, 0, 0];
    confidences.forEach(c => {
      const idx = Math.min(Math.floor(c * 5), 4);
      buckets[idx]++;
    });
    const maxBucket = Math.max(...buckets, 1);
    const distribution = buckets.map(b => (b / maxBucket) * 100);

    return { avg, high, medium, low, total: confidences.length, distribution };
  };

  const stats = getConfidenceStats();

  // Use actual engine status from backend health check; never guess from confidence scores
  const classificationMethod = classificationEngine === 'bedrock' ? 'bedrock' : 'fallback';

  if (loading && !dailyReport && complaints.length === 0) {
    return (
      <div className="ai-insights-panel">
        <div className="ai-skeleton">
          <div className="skeleton skeleton-block"></div>
          <div className="skeleton skeleton-line"></div>
          <div className="skeleton skeleton-line short"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="ai-insights-panel">
      {/* Classification Method Status */}
      <div className="ai-section engine-section">
        <h3 className="ai-section-title">Classification Engine</h3>
        <div className={`ai-method-badge ${classificationMethod}`}>
          <span className="method-dot"></span>
          <span className="method-label">
            {classificationMethod === 'bedrock' ? '🤖 Bedrock AI Active' : '🔑 Keyword Fallback'}
          </span>
        </div>
        <p className="method-detail">
          {classificationMethod === 'bedrock'
            ? 'Using Amazon Bedrock Claude for classification'
            : 'Using keyword-based classification (configure AWS credentials for AI)'}
        </p>
      </div>

      {/* Confidence Distribution */}
      {stats.total > 0 && (
        <div className="ai-section">
          <h3 className="ai-section-title">Confidence Distribution</h3>
          <div className="confidence-summary">
            <div className="confidence-stat">
              <span className="stat-value">{(stats.avg * 100).toFixed(0)}%</span>
              <span className="stat-label">Average</span>
            </div>
            <div className="confidence-stat high">
              <span className="stat-value">{stats.high}</span>
              <span className="stat-label">High (&gt;80%)</span>
            </div>
            <div className="confidence-stat medium">
              <span className="stat-value">{stats.medium}</span>
              <span className="stat-label">Medium</span>
            </div>
            <div className="confidence-stat low">
              <span className="stat-value">{stats.low}</span>
              <span className="stat-label">Low (&lt;50%)</span>
            </div>
          </div>

          {/* Mini histogram */}
          <div className="confidence-histogram">
            {stats.distribution.map((height, i) => (
              <div key={i} className="histogram-bar-wrapper">
                <div
                  className="histogram-bar"
                  style={{ height: `${Math.max(height, 4)}%` }}
                  title={`${(i * 20)}%-${((i + 1) * 20)}%: ${Math.round(height)}%`}
                ></div>
                <span className="histogram-label">{i * 20}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Daily Report Summary */}
      <div className="ai-section report-section">
        <h3 className="ai-section-title">Daily AI Report</h3>
        {error && !dailyReport ? (
          <p className="report-error">{error}</p>
        ) : dailyReport ? (
          <div className="daily-report-summary">
            <div className="report-stats">
              <div className="report-stat">
                <span className="report-stat-value">{dailyReport.total_complaints}</span>
                <span className="report-stat-label">Complaints</span>
              </div>
              <div className="report-stat">
                <span className="report-stat-value">{dailyReport.high_risk_zones?.length || 0}</span>
                <span className="report-stat-label">High Risk Zones</span>
              </div>
              <div className="report-stat">
                <span className="report-stat-value">{dailyReport.predicted_incidents?.length || 0}</span>
                <span className="report-stat-label">Predictions</span>
              </div>
            </div>

            {dailyReport.ai_generated_summary && (
              <div className="report-ai-summary">
                <span className="summary-label">🤖 AI Analysis</span>
                <p className="summary-text">{dailyReport.ai_generated_summary}</p>
              </div>
            )}

            {dailyReport.weather_summary && (
              <div className="report-weather">
                <span className="summary-label">🌤️ Weather Impact</span>
                <p className="summary-text">{dailyReport.weather_summary}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="report-empty">No report available yet. Reports are generated daily.</p>
        )}
      </div>
    </div>
  );
};

export default AIInsightsPanel;
