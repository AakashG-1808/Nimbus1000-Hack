import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ComplaintForm from './ComplaintForm';
import { complaintsAPI } from '../services/api';

// Mock the API module
jest.mock('../services/api', () => ({
  complaintsAPI: {
    submitComplaint: jest.fn(),
  },
}));

/**
 * Integration tests for ComplaintForm
 * Tests the complete complaint submission flow
 * 
 * Validates: Requirements 1.1, 12.2
 */
describe('ComplaintForm Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('complete complaint submission flow with all validations', async () => {
    const mockOnSubmitSuccess = jest.fn();
    complaintsAPI.submitComplaint.mockResolvedValue({ 
      data: { success: true, complaint_id: 'test-123' } 
    });

    render(<ComplaintForm onSubmitSuccess={mockOnSubmitSuccess} />);

    // Step 1: Verify form renders
    expect(screen.getByText('Report a Complaint')).toBeInTheDocument();

    // Step 2: Try to submit empty form - should show validation error
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/please select a location/i)).toBeInTheDocument();
    });

    // Step 3: Fill in location only - should still show validation error
    const locationSelect = screen.getByLabelText(/location/i);
    fireEvent.change(locationSelect, { target: { value: 'Koramangala' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/please select a category/i)).toBeInTheDocument();
    });

    // Step 4: Fill in category - should still show validation error
    const categorySelect = screen.getByLabelText(/category/i);
    fireEvent.change(categorySelect, { target: { value: 'pothole' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/please provide a description/i)).toBeInTheDocument();
    });

    // Step 5: Fill in short description - should show length validation error
    const descriptionInput = screen.getByLabelText(/description/i);
    fireEvent.change(descriptionInput, { target: { value: 'short' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/description must be at least 10 characters/i)).toBeInTheDocument();
    });

    // Step 6: Fill in valid description and submit successfully
    fireEvent.change(descriptionInput, { 
      target: { value: 'There is a large pothole on the main road causing traffic issues and damage to vehicles' } 
    });
    fireEvent.click(submitButton);

    // Verify API was called with correct data
    await waitFor(() => {
      expect(complaintsAPI.submitComplaint).toHaveBeenCalledWith(
        expect.objectContaining({
          location: 'Koramangala',
          category: 'pothole',
          description: 'There is a large pothole on the main road causing traffic issues and damage to vehicles',
          timestamp: expect.any(String),
        })
      );
    });

    // Verify success message is shown
    await waitFor(() => {
      expect(screen.getByText(/complaint submitted successfully/i)).toBeInTheDocument();
    });

    // Verify form is reset
    expect(locationSelect.value).toBe('');
    expect(categorySelect.value).toBe('');
    expect(descriptionInput.value).toBe('');

    // Verify callback is called after delay
    await waitFor(() => {
      expect(mockOnSubmitSuccess).toHaveBeenCalled();
    }, { timeout: 2000 });
  });

  test('handles network errors gracefully', async () => {
    complaintsAPI.submitComplaint.mockRejectedValue(
      new Error('Network error')
    );

    render(<ComplaintForm />);

    // Fill in valid form data
    const locationSelect = screen.getByLabelText(/location/i);
    const categorySelect = screen.getByLabelText(/category/i);
    const descriptionInput = screen.getByLabelText(/description/i);

    fireEvent.change(locationSelect, { target: { value: 'Indiranagar' } });
    fireEvent.change(categorySelect, { target: { value: 'flooding' } });
    fireEvent.change(descriptionInput, { 
      target: { value: 'Heavy waterlogging on the main street after rain' } 
    });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);

    // Verify error message is shown
    await waitFor(() => {
      expect(screen.getByText(/error: network error/i)).toBeInTheDocument();
    });

    // Verify form data is preserved (not reset on error)
    expect(locationSelect.value).toBe('Indiranagar');
    expect(categorySelect.value).toBe('flooding');
    expect(descriptionInput.value).toBe('Heavy waterlogging on the main street after rain');
  });

  test('validates all 8 complaint categories are available', () => {
    render(<ComplaintForm />);

    const categorySelect = screen.getByLabelText(/category/i);
    const options = Array.from(categorySelect.options)
      .map(opt => opt.value)
      .filter(v => v);

    const expectedCategories = [
      'pothole',
      'flooding',
      'traffic',
      'garbage',
      'streetlight',
      'water_supply',
      'noise',
      'construction'
    ];

    expectedCategories.forEach(category => {
      expect(options).toContain(category);
    });

    expect(options).toHaveLength(8);
  });

  test('validates 40+ Bengaluru locations are available', () => {
    render(<ComplaintForm />);

    const locationSelect = screen.getByLabelText(/location/i);
    const options = Array.from(locationSelect.options)
      .map(opt => opt.value)
      .filter(v => v);

    // Check for key locations
    const keyLocations = [
      'Koramangala',
      'Indiranagar',
      'Whitefield',
      'Electronic City',
      'Jayanagar',
      'Malleshwaram',
      'HSR Layout',
      'BTM Layout'
    ];

    keyLocations.forEach(location => {
      expect(options).toContain(location);
    });

    // Should have at least 40 locations
    expect(options.length).toBeGreaterThanOrEqual(40);
  });

  test('character counter updates as user types', () => {
    render(<ComplaintForm />);

    const descriptionInput = screen.getByLabelText(/description/i);
    const charCount = screen.getByText(/0 characters/i);

    expect(charCount).toBeInTheDocument();

    // Type some text
    fireEvent.change(descriptionInput, { 
      target: { value: 'Test description' } 
    });

    // Character count should update
    expect(screen.getByText(/16 characters/i)).toBeInTheDocument();
  });

  test('clears error message when user starts typing after validation error', async () => {
    render(<ComplaintForm />);

    // Try to submit empty form
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);

    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/please select a location/i)).toBeInTheDocument();
    });

    // Start typing in location field
    const locationSelect = screen.getByLabelText(/location/i);
    fireEvent.change(locationSelect, { target: { value: 'Koramangala' } });

    // Error message should be cleared
    await waitFor(() => {
      expect(screen.queryByText(/please select a location/i)).not.toBeInTheDocument();
    });
  });
});
