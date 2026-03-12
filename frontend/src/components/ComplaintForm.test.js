import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ComplaintForm from './ComplaintForm';
import { complaintsAPI } from '../services/api';

// Mock the API
jest.mock('../services/api', () => ({
  complaintsAPI: {
    submitComplaint: jest.fn(),
  },
}));

describe('ComplaintForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders complaint form with all required fields', () => {
    render(<ComplaintForm />);
    
    expect(screen.getByText('Report a Complaint')).toBeInTheDocument();
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit complaint/i })).toBeInTheDocument();
  });

  test('displays validation error when submitting empty form', async () => {
    render(<ComplaintForm />);
    
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/please select a location/i)).toBeInTheDocument();
    });
  });

  test('displays validation error when description is too short', async () => {
    render(<ComplaintForm />);
    
    // Fill in location and category
    const locationSelect = screen.getByLabelText(/location/i);
    const categorySelect = screen.getByLabelText(/category/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    
    fireEvent.change(locationSelect, { target: { value: 'Koramangala' } });
    fireEvent.change(categorySelect, { target: { value: 'pothole' } });
    fireEvent.change(descriptionInput, { target: { value: 'short' } });
    
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/description must be at least 10 characters/i)).toBeInTheDocument();
    });
  });

  test('submits form successfully with valid data', async () => {
    const mockOnSubmitSuccess = jest.fn();
    complaintsAPI.submitComplaint.mockResolvedValue({ data: { success: true } });
    
    render(<ComplaintForm onSubmitSuccess={mockOnSubmitSuccess} />);
    
    // Fill in all fields
    const locationSelect = screen.getByLabelText(/location/i);
    const categorySelect = screen.getByLabelText(/category/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    
    fireEvent.change(locationSelect, { target: { value: 'Koramangala' } });
    fireEvent.change(categorySelect, { target: { value: 'pothole' } });
    fireEvent.change(descriptionInput, { 
      target: { value: 'There is a large pothole on the main road causing traffic issues' } 
    });
    
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(complaintsAPI.submitComplaint).toHaveBeenCalledWith(
        expect.objectContaining({
          location: 'Koramangala',
          category: 'pothole',
          description: 'There is a large pothole on the main road causing traffic issues',
        })
      );
    });
    
    await waitFor(() => {
      expect(screen.getByText(/complaint submitted successfully/i)).toBeInTheDocument();
    });
    
    // Check that callback is called after delay
    await waitFor(() => {
      expect(mockOnSubmitSuccess).toHaveBeenCalled();
    }, { timeout: 2000 });
  });

  test('displays error message when API call fails', async () => {
    complaintsAPI.submitComplaint.mockRejectedValue({
      response: { data: { detail: 'Invalid location' } }
    });
    
    render(<ComplaintForm />);
    
    // Fill in all fields
    const locationSelect = screen.getByLabelText(/location/i);
    const categorySelect = screen.getByLabelText(/category/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    
    fireEvent.change(locationSelect, { target: { value: 'Koramangala' } });
    fireEvent.change(categorySelect, { target: { value: 'pothole' } });
    fireEvent.change(descriptionInput, { 
      target: { value: 'There is a large pothole on the main road' } 
    });
    
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid location/i)).toBeInTheDocument();
    });
  });

  test('resets form after successful submission', async () => {
    complaintsAPI.submitComplaint.mockResolvedValue({ data: { success: true } });
    
    render(<ComplaintForm />);
    
    // Fill in all fields
    const locationSelect = screen.getByLabelText(/location/i);
    const categorySelect = screen.getByLabelText(/category/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    
    fireEvent.change(locationSelect, { target: { value: 'Koramangala' } });
    fireEvent.change(categorySelect, { target: { value: 'pothole' } });
    fireEvent.change(descriptionInput, { 
      target: { value: 'There is a large pothole on the main road' } 
    });
    
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/complaint submitted successfully/i)).toBeInTheDocument();
    });
    
    // Check that form is reset
    expect(locationSelect.value).toBe('');
    expect(categorySelect.value).toBe('');
    expect(descriptionInput.value).toBe('');
  });

  test('disables form during submission', async () => {
    complaintsAPI.submitComplaint.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ data: { success: true } }), 100))
    );
    
    render(<ComplaintForm />);
    
    // Fill in all fields
    const locationSelect = screen.getByLabelText(/location/i);
    const categorySelect = screen.getByLabelText(/category/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    
    fireEvent.change(locationSelect, { target: { value: 'Koramangala' } });
    fireEvent.change(categorySelect, { target: { value: 'pothole' } });
    fireEvent.change(descriptionInput, { 
      target: { value: 'There is a large pothole on the main road' } 
    });
    
    const submitButton = screen.getByRole('button', { name: /submit complaint/i });
    fireEvent.click(submitButton);
    
    // Check that button shows submitting state
    expect(screen.getByRole('button', { name: /submitting/i })).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    
    await waitFor(() => {
      expect(screen.getByText(/complaint submitted successfully/i)).toBeInTheDocument();
    });
  });

  test('includes all 8 complaint categories', () => {
    render(<ComplaintForm />);
    
    const categorySelect = screen.getByLabelText(/category/i);
    const options = Array.from(categorySelect.options).map(opt => opt.value).filter(v => v);
    
    expect(options).toContain('pothole');
    expect(options).toContain('flooding');
    expect(options).toContain('traffic');
    expect(options).toContain('garbage');
    expect(options).toContain('streetlight');
    expect(options).toContain('water_supply');
    expect(options).toContain('noise');
    expect(options).toContain('construction');
    expect(options).toHaveLength(8);
  });

  test('includes multiple Bengaluru locations', () => {
    render(<ComplaintForm />);
    
    const locationSelect = screen.getByLabelText(/location/i);
    const options = Array.from(locationSelect.options).map(opt => opt.value).filter(v => v);
    
    // Check for some key locations
    expect(options).toContain('Koramangala');
    expect(options).toContain('Indiranagar');
    expect(options).toContain('Whitefield');
    expect(options).toContain('Electronic City');
    
    // Should have 40+ locations
    expect(options.length).toBeGreaterThanOrEqual(40);
  });
});
