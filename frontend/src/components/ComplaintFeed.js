import { useState, useEffect, useRef, useMemo } from 'react';
import { complaintsAPI } from '../services/api';
import './ComplaintFeed.css';

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
  const [search, setSearch] = useState('');
  const feedRef = useRef(null);
  const searchRef = useRef(null);

  // Reset expanded + search when tab changes
  useEffect(() => {
    setExpandedKey(null);
    setSearch('');
  }, [activeTab]);

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

  // Highlight matching text
  const highlight = (text, query) => {
    if (!query.trim()) return text;
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return text;
    return (
      <>
        {text.slice(0, idx)}
        <mark className="search-highlight">{text.slice(idx, idx + query.length)}</mark>
        {text.slice(idx + query.length)}
      </>
    );
  };

  // ── Filter helpers ────────────────────────────────────────────────────────
  const matchesSearch = (c, q) => {
    if (!q.trim()) return true;
    const lower = q.toLowerCase();
    return (
      c.location?.toLowerCase().includes(lower) ||
      c.category?.toLowerCase().includes(lower) ||
      fmtCat(c.category).toLowerCase().includes(lower) ||
      c.description?.toLowerCase().includes(lower)
    );
  };

  // ── Split + filter complaints ─────────────────────────────────────────────
  const pending = useMemo(() =>
    [...complaints]
      .filter(c => (c.status || 'open') === 'open')
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 50),
    [complaints]
  );

  const resolvedGroups = useMemo(() => {
    const resolved = complaints.filter(c => c.status === 'resolved');
    const map = new Map();
    for (const c of resolved) {
      const key = `${c.location}||${c.category}`;
      if (!map.has(key)) {
        map.set(key, { representative: c, count: 1 });
      } else {
        const g = map.get(key);
        g.count++;
        if (new Date(c.resolved_at) > new Date(g.representative.resolved_at)) {
          g.representative = c;
        }
      }
    }
    return [...map.entries()]
      .sort(([, a], [, b]) => new Date(b.representative.resolved_at || 0) - new Date(a.representative.resolved_at || 0))
      .map(([key, g]) => ({ key, ...g }));
  }, [complaints]);

  const filteredPending = useMemo(() =>
    pending.filter(c => matchesSearch(c, search)),
    [pending, search] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const filteredResolved = useMemo(() =>
    resolvedGroups.filter(({ representative: c }) => matchesSearch(c, search)),
    [resolvedGroups, search] // eslint-disable-line react-hooks/exhaustive-deps
  );

  // ── Resolve form helpers ──────────────────────────────────────────────────
  const getForm = (id) => resolveState[id] || { date: '', note: '', imageUrl: '', uploading: false, saving: false, error: null };
  const setForm = (id, patch) => setResolveState(p => ({ ...p, [id]: { ...getForm(id), ...patch } }));

  const handleImagePick = async (id, file) => {
    if (!file) return;
    setForm(id, { uploading: true, error: null });
    try {
      const res = await complaintsAPI.uploadImage(file);
      setForm(id, { imageUrl: res.data.url, uploading: false });
    } catch (e) {
      // S3 upload failed — fall back to local base64 data URL so the feature still works
      try {
        const dataUrl = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
        setForm(id, { imageUrl: dataUrl, uploading: false, error: null });
      } catch {
        const msg = e?.response?.data?.detail || e?.message || 'Upload failed';
        setForm(id, { uploading: false, error: `Image upload failed: ${msg}` });
      }
    }
  };

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
      setForm(complaint.complaint_id, { saving: false, error: null });
      setExpandedKey(null);
    } catch {
      setForm(complaint.complaint_id, { saving: false, error: 'Failed to save. Try again.' });
    }
  };

  const pendingCount = pending.length;
  const resolvedCount = resolvedGroups.length;

  // ── Pending card ──────────────────────────────────────────────────────────
  const renderPendingCard = (complaint) => {
    const isExpanded = expandedKey === complaint.complaint_id;
    const form = getForm(complaint.complaint_id);
    const badge = confidenceBadge(complaint.classification_confidence);

    return (
      <div key={complaint.complaint_id} className={`complaint-item ${catClass(complaint.category)}`}>
        <div
          className="complaint-summary"
          onClick={() => setExpandedKey(isExpanded ? null : complaint.complaint_id)}
          role="button" tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && setExpandedKey(isExpanded ? null : complaint.complaint_id)}
          aria-expanded={isExpanded}
        >
          <div className="complaint-header">
            <span className={`complaint-category ${catClass(complaint.category)}`}>
              {highlight(fmtCat(complaint.category), search)}
            </span>
            <div className="complaint-header-right">
              <span className="complaint-timestamp">{fmt(complaint.timestamp)}</span>
              <span className="expand-chevron">{isExpanded ? '▲' : '▼'}</span>
            </div>
          </div>
          <div className="complaint-location">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
            </svg>
            {highlight(complaint.location, search)}
          </div>
          {!isExpanded && (
            <div className="complaint-preview">
              {highlight(
                complaint.description.length > 90 ? complaint.description.slice(0, 90) + '…' : complaint.description,
                search
              )}
            </div>
          )}
        </div>

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
                  <label>
                    Attach Image
                    <div className="image-upload-row">
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp,image/gif"
                        id={`img-${complaint.complaint_id}`}
                        style={{ display: 'none' }}
                        onChange={e => handleImagePick(complaint.complaint_id, e.target.files[0])}
                      />
                      <label htmlFor={`img-${complaint.complaint_id}`} className="image-upload-btn">
                        {form.uploading
                          ? <><span className="btn-spinner" /> Uploading…</>
                          : '📎 Choose file'}
                      </label>
                      {form.imageUrl && !form.uploading && (
                        <a href={form.imageUrl} target="_blank" rel="noreferrer" className="image-preview-link">
                          ✅ Uploaded
                        </a>
                      )}
                    </div>
                  </label>
                  {form.error && <p className="resolve-error">{form.error}</p>}
                  <div className="resolve-actions">
                    <button className="resolve-btn save" disabled={form.saving || form.uploading} onClick={() => handleSave(complaint, false)}>
                      {form.saving
                        ? <><span className="btn-spinner" /> Saving…</>
                        : 'Save Details'}
                    </button>
                    <button className="resolve-btn mark-resolved" disabled={form.saving || form.uploading} onClick={() => handleSave(complaint, true)}>
                      {form.saving ? <><span className="btn-spinner" /> Working…</> : '✅ Mark as Resolved'}
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

  // ── Resolved card ─────────────────────────────────────────────────────────
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
            <span className={`complaint-category ${catClass(c.category)}`}>
              {highlight(fmtCat(c.category), search)}
            </span>
            <div className="complaint-header-right">
              {count > 1 && <span className="complaint-count-badge">{count}</span>}
              <span className="resolved-badge">✅ Resolved</span>
              <span className="expand-chevron">{isExpanded ? '▲' : '▼'}</span>
            </div>
          </div>
          <div className="complaint-location">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
            </svg>
            {highlight(c.location, search)}
          </div>
          {!isExpanded && (
            <div className="complaint-preview">
              {highlight(
                c.description.length > 90 ? c.description.slice(0, 90) + '…' : c.description,
                search
              )}
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

      {/* Search bar */}
      <div className="feed-search-wrap">
        <div className="feed-search-inner">
          <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            ref={searchRef}
            className="feed-search-input"
            type="text"
            placeholder="Search location, type, description…"
            value={search}
            onChange={e => { setSearch(e.target.value); setExpandedKey(null); }}
            aria-label="Search complaints"
          />
          {search && (
            <button className="search-clear" onClick={() => { setSearch(''); searchRef.current?.focus(); }} aria-label="Clear search">
              ×
            </button>
          )}
        </div>
        {search && (
          <span className="search-result-count">
            {activeTab === 'pending' ? filteredPending.length : filteredResolved.length} result{(activeTab === 'pending' ? filteredPending.length : filteredResolved.length) !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Feed list */}
      <div className="complaint-feed" ref={feedRef}>
        {/* Global loading overlay — shown when refreshing with existing data */}
        {loading && complaints.length > 0 && (
          <div className="feed-refresh-indicator">
            <span className="feed-spinner" /> Refreshing…
          </div>
        )}

        {/* Full loading state — no data yet */}
        {loading && complaints.length === 0 ? (
          <div className="feed-loading-state">
            <div className="feed-spinner-large" />
            <span>Loading complaints…</span>
          </div>
        ) : activeTab === 'pending' ? (
          filteredPending.length === 0
            ? <div className="complaint-feed-empty">
                {search ? `No pending complaints matching "${search}"` : 'No pending complaints'}
              </div>
            : filteredPending.map(renderPendingCard)
        ) : (
          filteredResolved.length === 0
            ? <div className="complaint-feed-empty">
                {search ? `No resolved complaints matching "${search}"` : 'No resolved complaints yet'}
              </div>
            : filteredResolved.map(renderResolvedCard)
        )}
      </div>

      {stale && <div className="stale-bar">⚠️ Showing stale data</div>}
      {error && complaints.length > 0 && <div className="stale-bar error-bar">{error}</div>}
    </div>
  );
};

export default ComplaintFeed;
