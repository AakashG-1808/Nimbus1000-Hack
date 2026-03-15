import React, { useState, useEffect, useRef } from 'react';
import { complaintsAPI } from '../services/api';
import './ComplaintFeed.css';

/**
 * ComplaintFeed component displays the 20 most recent complaints
 * Admins get a resolve panel per complaint.
 */
const ComplaintFeed = ({ complaints = [], loading = false, error = null, stale = false, isAdmin = false, onComplaintUpdate }) => {
  const [displayedComplaints, setDisplayedComplaints] = useState([]);
  const [previousComplaintIds, setPreviousComplaintIds] = useState(new Set());
  const [expandedId, setExpandedId] = useState(null);
  const [resolveState, setResolveState] = useState({}); // { [complaint_id]: { date, note, imageUrl, saving, error } }
  const feedRef = useRef(null);
  const shouldAutoScroll = useRef(true);

  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const complaintTime = new Date(timestamp);
    const diffMs = now - complaintTime;
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    if (diffSeconds < 60) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    return complaintTime.toLocaleDateString();
  };

  const getCategoryClass = (category) => {
    const categoryMap = {
      pothole: 'category-pothole', flooding: 'category-flooding',
      traffic: 'category-traffic', garbage: 'category-garbage',
      streetlight: 'category-streetlight', water_supply: 'category-water-supply',
      noise: 'category-noise', construction: 'category-construction'
    };
    return categoryMap[category] || 'category-default';
  };

  const formatCategory = (category) =>
    category.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

  const getConfidenceBadge = (confidence) => {
    if (confidence === undefined || confidence === null) return null;
    const percent = Math.round(confidence * 100);
    let className = 'confidence-badge';
    if (confidence >= 0.8) className += ' confidence-high';
    else if (confidence >= 0.5) className += ' confidence-medium';
    else className += ' confidence-low';
    return { className, percent, icon: confidence >= 0.8 ? '🤖' : '🔑' };
  };

  useEffect(() => {
    const sortedComplaints = [...complaints]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 20);
    const currentIds = new Set(sortedComplaints.map(c => c.complaint_id));
    const hasNewComplaints = sortedComplaints.some(c => !previousComplaintIds.has(c.complaint_id));
    setDisplayedComplaints(sortedComplaints);
    setPreviousComplaintIds(currentIds);
    if (hasNewComplaints && shouldAutoScroll.current && feedRef.current) {
      feedRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [complaints]);

  const handleScroll = () => {
    if (feedRef.current) {
      shouldAutoScroll.current = feedRef.current.scrollTop < 50;
    }
  };

  const getResolveForm = (id) => resolveState[id] || { date: '', note: '', imageUrl: '', saving: false, error: null };

  const updateResolveForm = (id, patch) =>
    setResolveState(prev => ({ ...prev, [id]: { ...getResolveForm(id), ...patch } }));

  const handleSave = async (complaint, markResolved) => {
    if (markResolved) {
      const confirmed = window.confirm(
        `Mark this complaint as resolved?\n\nCategory: ${formatCategory(complaint.category)}\nLocation: ${complaint.location}\n\nIt will be removed from the map for all users.`
      );
      if (!confirmed) return;
    }
    const form = getResolveForm(complaint.complaint_id);
    updateResolveForm(complaint.complaint_id, { saving: true, error: null });
    try {
      await complaintsAPI.resolveComplaint(complaint.complaint_id, {
        expected_resolution_date: form.date || null,
        resolution_note: form.note || null,
        image_url: form.imageUrl || null,
        mark_resolved: markResolved,
      });
      if (onComplaintUpdate) onComplaintUpdate();
      setExpandedId(null);
    } catch (e) {
      updateResolveForm(complaint.complaint_id, { saving: false, error: 'Failed to save. Try again.' });
    }
  };

  if (loading && displayedComplaints.length === 0) {
    return (
      <div className="complaint-feed">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="complaint-skeleton">
            <div className="skeleton skeleton-badge"></div>
            <div className="skeleton skeleton-line"></div>
            <div className="skeleton skeleton-line short"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error && displayedComplaints.length === 0) {
    return <div className="complaint-feed-empty error"><p>{error}</p></div>;
  }

  if (displayedComplaints.length === 0) {
    return (
      <div className="complaint-feed-empty">
        <p>No complaints to display</p>
        {stale && <span className="stale-indicator">Showing stale data</span>}
      </div>
    );
  }

  return (
    <div className="complaint-feed" ref={feedRef} onScroll={handleScroll}>
      {displayedComplaints.map((complaint) => {
        const form = getResolveForm(complaint.complaint_id);
        const isExpanded = expandedId === complaint.complaint_id;
        const isResolved = complaint.status === 'resolved';

        return (
          <div
            key={complaint.complaint_id}
            className={`complaint-item ${getCategoryClass(complaint.category)} ${isResolved ? 'complaint-resolved' : ''}`}
          >
            <div className="complaint-header">
              <span className={`complaint-category ${getCategoryClass(complaint.category)}`}>
                {formatCategory(complaint.category)}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {isResolved && <span className="resolved-badge">✅ Resolved</span>}
                <span className="complaint-timestamp">{formatTimestamp(complaint.timestamp)}</span>
              </div>
            </div>

            <div className="complaint-location">
              <svg className="location-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                <circle cx="12" cy="10" r="3"></circle>
              </svg>
              {complaint.location}
            </div>

            <div className="complaint-description">{complaint.description}</div>

            {complaint.expected_resolution_date && !isResolved && (
              <div className="complaint-eta">
                🗓️ Expected by: {new Date(complaint.expected_resolution_date).toLocaleDateString()}
              </div>
            )}

            {complaint.resolution_note && (
              <div className="complaint-resolution-note">📋 {complaint.resolution_note}</div>
            )}

            {complaint.image_url && (
              <div className="complaint-image">
                <img src={complaint.image_url} alt="Complaint" style={{ maxWidth: '100%', borderRadius: '6px', marginTop: '6px' }} />
              </div>
            )}

            {(() => {
              const badge = getConfidenceBadge(complaint.classification_confidence);
              if (!badge) return null;
              return (
                <div className={badge.className}>
                  <span>{badge.icon}</span>
                  <span>{badge.percent}%</span>
                </div>
              );
            })()}

            {/* Admin resolve panel */}
            {isAdmin && (
              <div className="admin-resolve-section">
                <button
                  className="admin-resolve-toggle"
                  onClick={() => setExpandedId(isExpanded ? null : complaint.complaint_id)}
                >
                  {isExpanded ? '▲ Close' : isResolved ? '✏️ Edit Resolution' : '🛠️ Manage'}
                </button>

                {isExpanded && (
                  <div className="admin-resolve-form">
                    <label>
                      Expected Resolution Date
                      <input
                        type="date"
                        value={form.date}
                        onChange={e => updateResolveForm(complaint.complaint_id, { date: e.target.value })}
                      />
                    </label>
                    <label>
                      Note
                      <textarea
                        rows={2}
                        placeholder="Add a resolution note..."
                        value={form.note}
                        onChange={e => updateResolveForm(complaint.complaint_id, { note: e.target.value })}
                      />
                    </label>
                    <label>
                      Image URL
                      <input
                        type="url"
                        placeholder="https://..."
                        value={form.imageUrl}
                        onChange={e => updateResolveForm(complaint.complaint_id, { imageUrl: e.target.value })}
                      />
                    </label>
                    {form.error && <p className="resolve-error">{form.error}</p>}
                    <div className="resolve-actions">
                      <button
                        className="resolve-btn save"
                        disabled={form.saving}
                        onClick={() => handleSave(complaint, false)}
                      >
                        {form.saving ? 'Saving...' : 'Save Details'}
                      </button>
                      {!isResolved && (
                        <button
                          className="resolve-btn mark-resolved"
                          disabled={form.saving}
                          onClick={() => handleSave(complaint, true)}
                        >
                          ✅ Mark as Resolved
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ComplaintFeed;
