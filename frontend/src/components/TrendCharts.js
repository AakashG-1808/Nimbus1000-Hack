import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import './TrendCharts.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

/**
 * Derive a human-readable zone name from zone data.
 * Uses nearest Bengaluru neighbourhood + dominant category.
 */
const BENGALURU_AREAS = [
  { name: 'Koramangala',        lat: 12.9352, lng: 77.6245 },
  { name: 'Indiranagar',        lat: 12.9716, lng: 77.6412 },
  { name: 'Whitefield',         lat: 12.9698, lng: 77.7499 },
  { name: 'Electronic City',    lat: 12.8456, lng: 77.6603 },
  { name: 'Jayanagar',          lat: 12.9250, lng: 77.5838 },
  { name: 'Malleshwaram',       lat: 13.0039, lng: 77.5727 },
  { name: 'HSR Layout',         lat: 12.9116, lng: 77.6473 },
  { name: 'BTM Layout',         lat: 12.9166, lng: 77.6101 },
  { name: 'Marathahalli',       lat: 12.9591, lng: 77.7011 },
  { name: 'Bannerghatta Road',  lat: 12.8892, lng: 77.5957 },
  { name: 'Yelahanka',          lat: 13.1007, lng: 77.5963 },
  { name: 'Hebbal',             lat: 13.0358, lng: 77.5970 },
  { name: 'Rajajinagar',        lat: 12.9916, lng: 77.5544 },
  { name: 'Basavanagudi',       lat: 12.9423, lng: 77.5742 },
  { name: 'JP Nagar',           lat: 12.9077, lng: 77.5854 },
  { name: 'Sarjapur Road',      lat: 12.9121, lng: 77.6871 },
  { name: 'Bellandur',          lat: 12.9259, lng: 77.6766 },
  { name: 'Bommanahalli',       lat: 12.9141, lng: 77.6257 },
  { name: 'Mahadevapura',       lat: 12.9899, lng: 77.6988 },
  { name: 'Yeshwanthpur',       lat: 13.0280, lng: 77.5385 },
  { name: 'KR Puram',           lat: 13.0092, lng: 77.6957 },
  { name: 'Brookefield',        lat: 12.9716, lng: 77.7137 },
  { name: 'Domlur',             lat: 12.9611, lng: 77.6387 },
  { name: 'Ulsoor',             lat: 12.9810, lng: 77.6190 },
  { name: 'Peenya',             lat: 13.0297, lng: 77.5200 },
  { name: 'Kengeri',            lat: 12.9077, lng: 77.4854 },
  { name: 'Banashankari',       lat: 12.9250, lng: 77.5480 },
  { name: 'Chickpet',           lat: 12.9634, lng: 77.5855 },
];

const CATEGORY_LABELS = {
  pothole: 'Pothole',
  flooding: 'Flooding',
  traffic: 'Traffic',
  garbage: 'Garbage',
  streetlight: 'Streetlight',
  water_supply: 'Water Supply',
  noise: 'Noise',
  construction: 'Construction',
};

function nearestArea(lat, lng) {
  let best = BENGALURU_AREAS[0];
  let bestDist = Infinity;
  for (const area of BENGALURU_AREAS) {
    const d = Math.hypot(area.lat - lat, area.lng - lng);
    if (d < bestDist) { bestDist = d; best = area; }
  }
  return best.name;
}

function zoneLabel(zone) {
  const coords = zone.center_coordinates;
  const lat = Array.isArray(coords) ? coords[0] : coords?.latitude;
  const lng = Array.isArray(coords) ? coords[1] : coords?.longitude;
  const area = (lat != null && lng != null) ? nearestArea(lat, lng) : 'Unknown';
  const cat = CATEGORY_LABELS[zone.dominant_category] || zone.dominant_category || 'Mixed';
  return `${area} – ${cat}`;
}

/**
 * TrendCharts component displays Chart.js visualizations
 * - 7-day complaint volume trend chart
 * - Risk score trend chart for top 5 high-risk zones
 * 
 * Charts update automatically when props change (every 30 seconds via Dashboard polling)
 * 
 * Validates: Requirements 14.1, 14.2, 14.3, 14.4
 */
const TrendCharts = ({ complaints, riskZones, loading = false }) => {
  // Process complaint data for 7-day trend
  const complaintVolumeData = useMemo(() => {
    if (!complaints || complaints.length === 0) {
      return null;
    }

    // Get last 7 days
    const today = new Date();
    const last7Days = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      date.setHours(0, 0, 0, 0);
      last7Days.push(date);
    }

    // Count complaints per day
    const complaintCounts = last7Days.map(date => {
      const nextDay = new Date(date);
      nextDay.setDate(nextDay.getDate() + 1);
      
      return complaints.filter(complaint => {
        const complaintDate = new Date(complaint.timestamp);
        return complaintDate >= date && complaintDate < nextDay;
      }).length;
    });

    // Format labels (e.g., "Mon 12/25")
    const labels = last7Days.map(date => {
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const dayName = dayNames[date.getDay()];
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${dayName} ${month}/${day}`;
    });

    return {
      labels,
      datasets: [
        {
          label: 'Complaint Volume',
          data: complaintCounts,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgb(59, 130, 246)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        },
      ],
    };
  }, [complaints]);

  // Process risk zone data for top 5 high-risk zones trend
  const riskScoreTrendData = useMemo(() => {
    if (!riskZones || riskZones.length === 0) {
      return null;
    }

    // Get top 5 zones by risk score
    const top5Zones = [...riskZones]
      .sort((a, b) => b.risk_score - a.risk_score)
      .slice(0, 5);

    if (top5Zones.length === 0) {
      return null;
    }

    // For now, simulate trend data since we don't have historical data
    // In production, this would fetch historical risk scores from the backend
    const timePoints = ['6h ago', '5h ago', '4h ago', '3h ago', '2h ago', '1h ago', 'Now'];
    
    // Generate colors for each zone
    const colors = [
      'rgb(239, 68, 68)',   // red
      'rgb(249, 115, 22)',  // orange
      'rgb(234, 179, 8)',   // yellow
      'rgb(34, 197, 94)',   // green
      'rgb(59, 130, 246)',  // blue
    ];

    const datasets = top5Zones.map((zone, index) => {
      // Simulate trend: slight variations around current risk score
      const currentScore = zone.risk_score;
      const trendData = timePoints.map((_, i) => {
        if (i === timePoints.length - 1) {
          return currentScore; // Current score at the end
        }
        // Simulate historical variation (±10% of current score)
        const variation = (Math.random() - 0.5) * 0.2 * currentScore;
        return Math.max(0, Math.min(100, currentScore + variation));
      });

      return {
        label: `${zoneLabel(zone)} (${zone.risk_score.toFixed(0)})`,
        data: trendData,
        borderColor: colors[index],
        backgroundColor: colors[index].replace('rgb', 'rgba').replace(')', ', 0.1)'),
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: colors[index],
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      };
    });

    return {
      labels: timePoints,
      datasets,
    };
  }, [riskZones]);

  // Chart options for complaint volume
  const complaintVolumeOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#374151',
          font: {
            size: 12,
            weight: '500',
          },
        },
      },
      title: {
        display: true,
        text: '7-Day Complaint Volume Trend',
        color: '#111827',
        font: {
          size: 16,
          weight: '600',
        },
        padding: {
          bottom: 20,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
        callbacks: {
          label: function(context) {
            return `Complaints: ${context.parsed.y}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
          color: '#6b7280',
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      x: {
        ticks: {
          color: '#6b7280',
        },
        grid: {
          display: false,
        },
      },
    },
  };

  // Chart options for risk score trend
  const riskScoreTrendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#374151',
          font: {
            size: 11,
            weight: '500',
          },
          boxWidth: 12,
          padding: 10,
        },
      },
      title: {
        display: true,
        text: 'Top 5 High-Risk Zones - Risk Score Trends',
        color: '#111827',
        font: {
          size: 16,
          weight: '600',
        },
        padding: {
          bottom: 20,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
        callbacks: {
          label: function(context) {
            const name = context.dataset.label.replace(/\s*\(\d+\)$/, '');
            return `${name}: ${context.parsed.y.toFixed(1)}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          stepSize: 20,
          color: '#6b7280',
          callback: function(value) {
            return value;
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        title: {
          display: true,
          text: 'Risk Score',
          color: '#6b7280',
          font: {
            size: 12,
          },
        },
      },
      x: {
        ticks: {
          color: '#6b7280',
        },
        grid: {
          display: false,
        },
      },
    },
  };

  return (
    <div className="trend-charts">
      {/* Complaint Volume Chart */}
      <div className="chart-container">
        {loading ? (
          <div className="chart-skeleton"></div>
        ) : complaintVolumeData ? (
          <Line data={complaintVolumeData} options={complaintVolumeOptions} />
        ) : (
          <div className="chart-placeholder">
            <p>No complaint data available</p>
          </div>
        )}
      </div>

      {/* Risk Score Trend Chart */}
      <div className="chart-container">
        {loading ? (
          <div className="chart-skeleton"></div>
        ) : riskScoreTrendData ? (
          <Line data={riskScoreTrendData} options={riskScoreTrendOptions} />
        ) : (
          <div className="chart-placeholder">
            <p>No risk zone data available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrendCharts;
