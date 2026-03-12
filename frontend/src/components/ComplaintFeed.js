import React, { useState, useEffect, useRef } from 'react';
import './ComplaintFeed.css';

/**
 * ComplaintFeed component displays the 20 most recent complaints
 * with auto-scroll functionality for new complaints
 * 
 * Validates: Requirements 13.1, 13.2, 13.3, 13.4
 */
const ComplaintFeed = ({ complaints = [] }) => {
  const [displayedComplaints, setDisplayedComplaints] = useState([]);
  const [previousComplaintIds, setPreviousComplaintIds] = useState(new Set());
  const feedRef = useRef(null);
  const shouldAutoScroll = useRef(true);

  // Format timestamp to relative time (e.g., "2 minutes ago")
  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const complaintTime = new Date(timestamp);
    const diffMs = now - complaintTime;
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) {
      return 'Just now';
    } else if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return complaintTime.toLocaleDateString();
    }
  };

  // Get category-specific styling class
  const getCategoryClass = (category) => {
    const categoryMap = {
      'pothole': 'category-pothole',
      'flooding': 'category-flooding',
      'traffic': 'category-traffic',
      'garbage': 'category-garbage',
      'streetlight': 'category-streetlight',
      'water_supply': 'category-water-supply',
      'noise': 'category-noise',
      'construction': 'category-construction'
    };
    return categoryMap[category] || 'category-default';
  };

  // Format category for display (e.g., "water_supply" -> "Water Supply")
  const formatCategory = (category) => {
    return category
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Update displayed complaints when complaints prop changes
  useEffect(() => {
    // Sort by timestamp descending and take the 20 most recent
    const sortedComplaints = [...complaints]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 20);

    // Check for new complaints
    const currentIds = new Set(sortedComplaints.map(c => c.complaint_id));
    const hasNewComplaints = sortedComplaints.some(
      c => !previousComplaintIds.has(c.complaint_id)
    );

    setDisplayedComplaints(sortedComplaints);
    setPreviousComplaintIds(currentIds);

    // Auto-scroll to top if there are new complaints
    if (hasNewComplaints && shouldAutoScroll.current && feedRef.current) {
      feedRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }, [complaints]);

  // Handle manual scroll - disable auto-scroll if user scrolls away from top
  const handleScroll = () => {
    if (feedRef.current) {
      const isAtTop = feedRef.current.scrollTop < 50;
      shouldAutoScroll.current = isAtTop;
    }
  };

  if (displayedComplaints.length === 0) {
    return (
      <div className="complaint-feed-empty">
        <p>No complaints to display</p>
      </div>
    );
  }

  return (
    <div 
      className="complaint-feed" 
      ref={feedRef}
      onScroll={handleScroll}
    >
      {displayedComplaints.map((complaint) => (
        <div 
          key={complaint.complaint_id} 
          className={`complaint-item ${getCategoryClass(complaint.category)}`}
        >
          <div className="complaint-header">
            <span className={`complaint-category ${getCategoryClass(complaint.category)}`}>
              {formatCategory(complaint.category)}
            </span>
            <span className="complaint-timestamp">
              {formatTimestamp(complaint.timestamp)}
            </span>
          </div>
          
          <div className="complaint-location">
            <svg 
              className="location-icon" 
              width="14" 
              height="14" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            {complaint.location}
          </div>
          
          <div className="complaint-description">
            {complaint.description}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ComplaintFeed;
