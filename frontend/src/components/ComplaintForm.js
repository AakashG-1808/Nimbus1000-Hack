import React, { useState } from 'react';
import { complaintsAPI } from '../services/api';
import './ComplaintForm.css';

/**
 * ComplaintForm component for submitting citizen complaints
 * 
 * Features:
 * - Location dropdown (40+ Bengaluru locations)
 * - Category dropdown (8 supported categories)
 * - Description textarea
 * - Form validation
 * - Success/error message display
 * - Triggers dashboard refresh on successful submission
 * 
 * Validates: Requirements 1.1, 12.2
 */
const ComplaintForm = ({ onSubmitSuccess }) => {
  // Form state
  const [formData, setFormData] = useState({
    location: '',
    category: '',
    description: '',
  });

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState(null);
  const [messageType, setMessageType] = useState(null); // 'success' or 'error'

  // Bengaluru locations (40+ locations)
  const locations = [
    "Koramangala", "Indiranagar", "Whitefield", "Electronic City",
    "Jayanagar", "Malleshwaram", "HSR Layout", "BTM Layout",
    "Marathahalli", "Bannerghatta Road", "Yelahanka", "Hebbal",
    "Rajajinagar", "Basavanagudi", "JP Nagar", "Sarjapur Road",
    "Bellandur", "Bommanahalli", "Mahadevapura", "Yeshwanthpur",
    "KR Puram", "Ramamurthy Nagar", "CV Raman Nagar", "Hoodi",
    "Varthur", "Kadugodi", "Brookefield", "Domlur",
    "Ulsoor", "Frazer Town", "Richmond Town", "Shivajinagar",
    "Sadashivanagar", "Vijayanagar", "Peenya", "Jalahalli",
    "Nagarbhavi", "Kengeri", "Banashankari", "Girinagar",
    "Uttarahalli", "Rajarajeshwari Nagar", "Chickpet", "Shantinagar"
  ];

  // Complaint categories (8 supported types)
  const categories = [
    { value: 'pothole', label: 'Pothole' },
    { value: 'flooding', label: 'Flooding' },
    { value: 'traffic', label: 'Traffic' },
    { value: 'garbage', label: 'Garbage' },
    { value: 'streetlight', label: 'Street Light' },
    { value: 'water_supply', label: 'Water Supply' },
    { value: 'noise', label: 'Noise' },
    { value: 'construction', label: 'Construction' },
  ];

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear message when user starts typing
    if (message) {
      setMessage(null);
      setMessageType(null);
    }
  };

  // Validate form
  const validateForm = () => {
    if (!formData.location) {
      setMessage('Please select a location');
      setMessageType('error');
      return false;
    }
    if (!formData.category) {
      setMessage('Please select a category');
      setMessageType('error');
      return false;
    }
    if (!formData.description.trim()) {
      setMessage('Please provide a description');
      setMessageType('error');
      return false;
    }
    if (formData.description.trim().length < 10) {
      setMessage('Description must be at least 10 characters');
      setMessageType('error');
      return false;
    }
    return true;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setMessage(null);
    setMessageType(null);

    try {
      // Submit complaint to backend
      const complaintData = {
        location: formData.location,
        category: formData.category,
        description: formData.description.trim(),
        timestamp: new Date().toISOString(),
      };

      const response = await complaintsAPI.submitComplaint(complaintData);

      // Show success message
      setMessage('Complaint submitted successfully!');
      setMessageType('success');

      // Reset form
      setFormData({
        location: '',
        category: '',
        description: '',
      });

      // Trigger dashboard refresh if callback provided
      if (onSubmitSuccess) {
        // Wait a moment to ensure backend has processed the complaint
        setTimeout(() => {
          onSubmitSuccess();
        }, 1000);
      }

    } catch (error) {
      console.error('Error submitting complaint:', error);
      
      // Show error message
      let errorMessage = 'Failed to submit complaint. Please try again.';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = `Error: ${error.message}`;
      }

      setMessage(errorMessage);
      setMessageType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="complaint-form-container">
      <h2>Report a Complaint</h2>
      <p className="form-description">
        Help us improve Bengaluru by reporting infrastructure issues in your area.
      </p>

      <form onSubmit={handleSubmit} className="complaint-form">
        {/* Location dropdown */}
        <div className="form-group">
          <label htmlFor="location">
            Location <span className="required">*</span>
          </label>
          <select
            id="location"
            name="location"
            value={formData.location}
            onChange={handleChange}
            disabled={isSubmitting}
            required
          >
            <option value="">Select a location</option>
            {locations.map(location => (
              <option key={location} value={location}>
                {location}
              </option>
            ))}
          </select>
        </div>

        {/* Category dropdown */}
        <div className="form-group">
          <label htmlFor="category">
            Category <span className="required">*</span>
          </label>
          <select
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            disabled={isSubmitting}
            required
          >
            <option value="">Select a category</option>
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        {/* Description textarea */}
        <div className="form-group">
          <label htmlFor="description">
            Description <span className="required">*</span>
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Describe the issue in detail..."
            rows="4"
            disabled={isSubmitting}
            required
          />
          <div className="char-count">
            {formData.description.length} characters
          </div>
        </div>

        {/* Message display */}
        {message && (
          <div className={`form-message ${messageType}`}>
            {messageType === 'success' ? '✓ ' : '✗ '}
            {message}
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          className="submit-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Complaint'}
        </button>
      </form>
    </div>
  );
};

export default ComplaintForm;
