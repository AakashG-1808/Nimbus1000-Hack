import { useState, useEffect, useRef, useMemo } from 'react';
import { complaintsAPI } from '../services/api';
import './ComplaintFeed.css';

/**
 * ComplaintFeed — tabbed pending / resolved complaint list.
 * Resolved complaints are deduplicated by location+category (showing count).
 * Every item is click-to-expand for full details.
 * Admins get the manage/resolve form on pending items.
 */
const ComplaintFeed = ({
  complaints = [],
  loading = false,
  error = null,
  stale = false,
  isAdmin = false,
  onComplaintUpdate,
}) => {
  const [activeTab, setActiveTab] = useState('pending');
  const [expandedKey, setExpandedKey] = useState(null);
  const [resolveState, setResolveState] = useState({});
  const feedRef = useRef(null);

  // Reset expanded item when tab changes
  useEffect(() => { setExpandedKey(null); }, [activeTab]);

  // ── Helpers ───────────────────────────────────────────────────────────────
  const fmt = (ts) => {
    const d = new Date(ts), now = new Date();
    const s = Math.floor((now - d) / 1000);
    if (s < 60) return 'Just now';
    if (s < 3600) return `${Math.floor(s / 60)}m ago`;
    if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
    const days = Math.floor(s / 86400);
    return days < 7 ? `${days}d ago` : d.toLocaleDateString();
  };

  const catClass = (c) => ({
    pothole: 'category-pothole', flooding: 'category-flooding',
    traffic: 'category-traffic', garbage: 'category-garbage',
    streetlight: 'category-streetlight', water_supply: 'category-water-supply',
    noise: 'category-noise', construction: 'category-construction',
  }[c] || 'category-default');

  const fmtCat = (c) => c.split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ');

  const confidenceBadge = (conf) => {
    if (conf == null) return null;
    const pct = Math.round(conf * 100);
    const cls = conf >= 0.8 ? 'confidence-high' : conf >= 0.5 ? 'confidence-medium' : 'confidence-low';
    return { pct, cls, icon: conf >= 0.8 ? '🤖' : '🔑' };
  };

  // ── Split complaints ──────────────────────────────────────────────────────
  const pending = useMemo(() =>
    [...complaints]
      .filter(c => (c.status || 'open') === 'open')
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 50),
    [complaints]
  );

  // Deduplicate resolved by location+category — keep the most-recent per group
  const resolvedGroups = useMemo(() => {
    const resolved = complaints.filter(c => c.status === 'resolved');
    const map = new Map();
    for (const c of resolved) {
      const key = `${c.location}||${c.category}`;
      if (!map.has(key)) {
        map.set(key, { representative: c, count: 1, all: [c] });
      } else {
        const g = map.get(key);
        g.count++;
        g.all.push(c);
        // Keep the most recently resolved as representative
        if (new Date(c.resolved_at) > new Date(g.representative.resolved_at)) {
          g.representative = c;
        }
      }
    }
    return [...map.entries()]
      .sort(([, a], [, b]) => new Date(b.representative.resolved_at || 0) - new Date(a.representative.resolved_at || 0))
      .map(([key, g]) => ({ key, ...g }));
  }, [complaints]);

  // ── Resolve form helpers ──────────────────────────────────────────────────
  const getForm = (id) => resolveState[id] || { date: '', note: '', imageUrl: '', saving: false, error: null };
  const setForm = (id, patch) => setResolveState(p => ({ ...p, [id]: { ...getForm(id), ...patch } }));

  const handleSave = async (complaint, markResolved) => {
    if (markResolved) {
      const confirmed = window.confirm(
        `Mark as resolved?\n\nCategory: ${fmtCat(complaint.category)}\nLocation: ${complaint.location}\n\nAll open complaints of the same type at this location will be resolved and removed from the map.`
      );
      if (!confirmed) return;
    }
    const form = getForm(complaint.complaint_id);
    setForm(complaint.complaint_id, { saving: true, error: null });
    try {
      await complaintsAPI.resolveComplaint(complaint.complaint_id, {
        expected_resolution_date: form.date || null,
        resolution_note: form.note || null,
        image_url: form.imageUrl || null,
        mark_resolved: markResolved,
      });
      if (onComplaintUpdate) onComplaintUpdate();
      setExpandedKey(null);
    } catch {
      setForm(complaint.complaint_id, { saving: false, error: 'Failed to save. Try again.' });
    }
  };

  // ── Counts for tab badges ─────────────────────────────────────────────────
  const pendingCount = pending.length;
  const resolvedCount = resolvedGroups.length;

  // ── Loading / error states ────────────────────────────────────────────────
  if (loading && complaints.length === 0) {
    return (
      <div className="complaint-feed-wrap">
        <div className="feed-tabs">
          <button className="feed-tab active">Pending</button>
          <button className="feed-tab">Resolved</button>
        </div>
        <div className="complaint-feed">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="complaint-skeleton">
              <div className="skeleton skeleton-badge" />
              <div className="skeleton skeleton-line" />
              <div className="skeleton skeleton-line short" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Render a single complaint card ────────────────────────────────────────
  const renderPendingCard = (complaint) => {
    const isExpanded = expandedKey === complaint.complaint_id;
    const form = getForm(complaint.complaint_id);
    const badge = confidenceBadge(complaint.classification_confidence);

    return (
      <div key={complaint.complaint_id} className={`complaint-item ${catClass(complaint.category)}`}>
        {/* Summary row — always visible */}
        <div
          className="complaint-summary"
          onClick={() => setExpandedKey(isExpanded ? null : complaint.complaint_id)}
          role="button" tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && setExpandedKey(isExpanded ? null : complaint.complaint_id)}
          aria-expanded={isExpanded}
        >
          <div className="complaint-header">
            <span className={`complaint-category ${catClass(complaint.category)}`}>{fmtCat(complaint.category)}</span>
            <div className="complaint-header-right">
              <span className="complaint-timestamp">{fmt(complaint.timestamp)}</span>
              <span className="expand-chevron">{isExpanded ? '▲' : '▼'}</span>
            </div>
          </div>
          <div className="complaint-location">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
            </svg>
            {complaint.location}
          </div>
          {!isExpanded && (
            <div className="complaint-preview">
              {complaint.description.length > 90 ? complaint.description.slice(0, 90) + '…' : complaint.description}
            </div>
          )}
        </div>

        {/* Expanded detail */}
        {isExpanded && (
          <div className="complaint-detail">
            <p className="complaint-description">{complaint.description}</p>
            {badge && (
              <span className={`confidence-badge ${badge.cls}`}>{badge.icon} {badge.pct}% confidence</span>
            )}
            {complaint.expected_resolution_date && (
              <div className="detail-row">🗓️ Expected by: {new Date(complaint.expected_resolution_date).toLocaleDateString()}</div>
            )}
            {complaint.resolution_note && (
              <div className="detail-row">📋 {complaint.resolution_note}</div>
            )}
            <div className="complaint-id-label">ID: {complaint.complaint_id.slice(0, 8)}…</div>

            {/* Admin manage panel */}
            {isAdmin && (
              <div className="admin-resolve-section">
                <div className="admin-resolve-form">
                  <label>Expected Resolution Date
                    <input type="date" value={form.date} onChange={e => setForm(complaint.complaint_id, { date: e.target.value })} />
                  </label>
                  <label>Note
                    <textarea rows={2} placeholder="Add a resolution note…" value={form.note}
                      onChange={e => setForm(complaint.complaint_id, { note: e.target.value })} />
                  </label>
                  <label>Image URL
                    <input type="url" placeholder="https://…" value={form.imageUrl}
                      onChange={e => setForm(complaint.complaint_id, { imageUrl: e.target.value })} />
                  </label>
                  {form.error && <p className="resolve-error">{form.error}</p>}
                  <div className="resolve-actions">
                    <button className="resolve-btn save" disabled={form.saving} onClick={() => handleSave(complaint, false)}>
                      {form.saving ? 'Saving…' : 'Save Details'}
                    </button>
                    <button className="resolve-btn mark-resolved" disabled={form.saving} onClick={() => handleSave(complaint, true)}>
                      ✅ Mark as Resolved
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderResolvedCard = ({ key, representative: c, count }) => {
    const isExpanded = expandedKey === key;
    return (
      <div key={key} className={`complaint-item complaint-resolved ${catClass(c.category)}`}>
        <div
          className="complaint-summary"
          onClick={() => setExpandedKey(isExpanded ? null : key)}
          role="button" tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && setExpandedKey(isExpanded ? null : key)}
          aria-expanded={isExpanded}
        >
          <div className="complaint-header">
            <span className={`complaint-category ${catClass(c.category)}`}>{fmtCat(c.category)}</span>
            <div className="complaint-header-right">
              {count > 1 && <span className="complaint-count-badge">{count} complaints</span>}
              <span className="resolved-badge">✅ Resolved</span>
              <span className="expand-chevron">{isExpanded ? '▲' : '▼'}</span>
            </div>
          </div>
          <div className="complaint-location">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
            </svg>
            {c.location}
          </div>
          {!isExpanded && (
            <div className="complaint-preview">
              {c.description.length > 90 ? c.description.slice(0, 90) + '…' : c.description}
            </div>
          )}
        </div>

        {isExpanded && (
          <div className="complaint-detail">
            {count > 1 && (
              <div className="detail-row resolved-group-note">
                🔁 {count} complaints at this location were resolved together.
              </div>
            )}
            <p className="complaint-description">{c.description}</p>
            {c.resolved_at && (
              <div className="detail-row resolved-at">✅ Resolved on: {new Date(c.resolved_at).toLocaleString()}</div>
            )}
            {c.expected_resolution_date && (
              <div className="detail-row">🗓️ Expected by: {new Date(c.expected_resolution_date).toLocaleDateString()}</div>
            )}
            {c.resolution_note && (
              <div className="detail-row">📋 {c.resolution_note}</div>
            )}
            {c.image_url && (
              <img src={c.image_url} alt="Resolution attachment" className="complaint-attachment" />
            )}
            <div className="complaint-id-label">ID: {c.complaint_id.slice(0, 8)}…</div>
          </div>
        )}
      </div>
    );
  };

  // ── Main render ───────────────────────────────────────────────────────────
  return (
    <div className="complaint-feed-wrap">
      {/* Tab bar */}
      <div className="feed-tabs">
        <button
          className={`feed-tab ${activeTab === 'pending' ? 'active' : ''}`}
          onClick={() => setActiveTab('pending')}
        >
          Pending
          {pendingCount > 0 && <span className="tab-badge tab-badge-pending">{pendingCount}</span>}
        </button>
        <button
          className={`feed-tab ${activeTab === 'resolved' ? 'active' : ''}`}
          onClick={() => setActiveTab('resolved')}
        >
          Resolved
          {resolvedCount > 0 && <span className="tab-badge tab-badge-resolved">{resolvedCount}</span>}
        </button>
      </div>

      {/* Feed list */}
      <div className="complaint-feed" ref={feedRef}>
        {activeTab === 'pending' && (
          pending.length === 0
            ? <div className="complaint-feed-empty"><p>No pending complaints</p></div>
            : pending.map(renderPendingCard)
        )}
        {activeTab === 'resolved' && (
          resolvedGroups.length === 0
            ? <div className="complaint-feed-empty"><p>No resolved complaints yet</p></div>
            : resolvedGroups.map(renderResolvedCard)
        )}
      </div>

      {stale && <div className="stale-bar">⚠️ Showing stale data</div>}
      {error && complaints.length > 0 && <div className="stale-bar error-bar">{error}</div>}
    </div>
  );
};

export default ComplaintFeed;
