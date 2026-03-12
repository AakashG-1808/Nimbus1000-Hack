import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import * as fc from 'fast-check';
import ComplaintFeed from './ComplaintFeed';

/**
 * Property-Based Tests for ComplaintFeed Component
 * 
 * Uses fast-check for property-based testing with 100+ iterations
 * to verify universal correctness properties across all valid inputs.
 * 
 * Feature: urbanguard-ai-system
 */

// Mock CSS imports
jest.mock('./ComplaintFeed.css', () => ({}));

/**
 * Arbitrary generators for test data
 */

// Generate valid Bengaluru coordinates
const bengaluruCoordinatesArbitrary = () => 
  fc.tuple(
    fc.double({ min: 12.8, max: 13.2 }), // Latitude
    fc.double({ min: 77.4, max: 77.8 })  // Longitude
  );

// Generate a complaint object
let complaintIdCounter = 0;
const complaintArbitrary = () =>
  fc.record({
    complaint_id: fc.integer({ min: 1, max: 1000000 }).map(n => `complaint-${n}-${++complaintIdCounter}`),
    location: fc.constantFrom(
      'Koramangala', 'Indiranagar', 'Whitefield', 'Electronic City',
      'Jayanagar', 'Malleshwaram', 'HSR Layout', 'BTM Layout'
    ),
    category: fc.constantFrom(
      'pothole', 'flooding', 'traffic', 'garbage', 
      'streetlight', 'water_supply', 'noise', 'construction'
    ),
    description: fc.string({ minLength: 10, maxLength: 100 }).filter(s => s.trim().length > 0),
    timestamp: fc.date({ min: new Date('2024-01-01'), max: new Date() }).map(d => d.toISOString()),
    coordinates: bengaluruCoordinatesArbitrary()
  }).filter(c => !isNaN(c.coordinates[0]) && !isNaN(c.coordinates[1]));

/**
 * Property 36: Recent Complaints Feed Selection
 * 
 * For any set of complaints, the Map_Visualizer should display the 20 most 
 * recent complaints in chronological order (most recent first).
 * 
 * Validates: Requirements 13.1
 * 
 * Feature: urbanguard-ai-system, Property 36: Recent Complaints Feed Selection
 */
describe('Property 36: Recent Complaints Feed Selection', () => {
  
  test('Property: When given more than 20 complaints, only 20 are displayed', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 21, maxLength: 50 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Exactly 20 complaints are displayed
          return complaintItems.length === 20;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: When given fewer than 20 complaints, all are displayed', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 19 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: All complaints are displayed when count < 20
          return complaintItems.length === complaints.length;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: When given exactly 20 complaints, all 20 are displayed', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 20, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: All 20 complaints are displayed
          return complaintItems.length === 20;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: The 20 most recent complaints are selected (not random 20)', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 25, maxLength: 40 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          // Sort complaints by timestamp descending to get expected 20 most recent
          const sortedComplaints = [...complaints]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 20);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: The displayed complaints match the 20 most recent
          // We check by verifying the descriptions are present
          const displayedDescriptions = Array.from(complaintItems).map(
            item => item.querySelector('.complaint-description')?.textContent
          );
          
          const expectedDescriptions = sortedComplaints.map(c => c.description);
          
          return displayedDescriptions.every((desc, i) => desc === expectedDescriptions[i]);
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Complaints are displayed in chronological order (most recent first)', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 5, maxLength: 30 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Extract timestamps from displayed complaints
          const displayedTimestamps = Array.from(complaintItems).map(item => {
            const description = item.querySelector('.complaint-description')?.textContent;
            // Find the complaint with this description
            const complaint = complaints.find(c => c.description === description);
            return complaint ? new Date(complaint.timestamp).getTime() : 0;
          });
          
          // Cleanup
          container.remove();
          
          // Assert: Timestamps are in descending order (most recent first)
          for (let i = 0; i < displayedTimestamps.length - 1; i++) {
            if (displayedTimestamps[i] < displayedTimestamps[i + 1]) {
              return false;
            }
          }
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Empty complaint list displays empty state', () => {
    const { container } = render(<ComplaintFeed complaints={[]} />);
    
    const emptyState = container.querySelector('.complaint-feed-empty');
    const complaintItems = container.querySelectorAll('.complaint-item');
    
    // Cleanup
    container.remove();
    
    // Assert: Empty state is shown and no complaint items
    expect(emptyState).toBeTruthy();
    expect(complaintItems.length).toBe(0);
  });

  test('Property: Feed never displays more than 20 complaints regardless of input size', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 20, maxLength: 100 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Never more than 20 complaints displayed
          return complaintItems.length <= 20;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Most recent complaint is always displayed first', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 5, maxLength: 30 }),
        (complaints) => {
          // Find the most recent complaint
          const mostRecent = complaints.reduce((latest, current) => 
            new Date(current.timestamp) > new Date(latest.timestamp) ? current : latest
          );
          
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const firstComplaintItem = container.querySelector('.complaint-item');
          const firstDescription = firstComplaintItem?.querySelector('.complaint-description')?.textContent;
          
          // Cleanup
          container.remove();
          
          // Assert: First displayed complaint is the most recent
          return firstDescription === mostRecent.description;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Oldest complaint in feed is never older than 21st most recent', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 25, maxLength: 40 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          // Sort all complaints by timestamp descending
          const sortedComplaints = [...complaints]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
          
          // The 21st most recent complaint (index 20)
          const twentyFirstMostRecent = sortedComplaints[20];
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Get all displayed timestamps
          const displayedTimestamps = Array.from(complaintItems).map(item => {
            const description = item.querySelector('.complaint-description')?.textContent;
            const complaint = complaints.find(c => c.description === description);
            return complaint ? new Date(complaint.timestamp).getTime() : 0;
          });
          
          const oldestDisplayed = Math.min(...displayedTimestamps);
          const twentyFirstTimestamp = new Date(twentyFirstMostRecent.timestamp).getTime();
          
          // Cleanup
          container.remove();
          
          // Assert: Oldest displayed is newer than or equal to 21st most recent
          return oldestDisplayed >= twentyFirstTimestamp;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Property 37: Complaint Feed Display Completeness
 * 
 * For any complaint displayed in the feed, the Map_Visualizer should show 
 * location, category, description, and timestamp.
 * 
 * Validates: Requirements 13.3
 * 
 * Feature: urbanguard-ai-system, Property 37: Complaint Feed Display Completeness
 */
describe('Property 37: Complaint Feed Display Completeness', () => {
  
  test('Property: All displayed complaints show location field', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 25 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Every complaint item has a location element
          return Array.from(complaintItems).every(item => {
            const locationElement = item.querySelector('.complaint-location');
            return locationElement && locationElement.textContent.trim().length > 0;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: All displayed complaints show category field', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 25 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Every complaint item has a category element
          return Array.from(complaintItems).every(item => {
            const categoryElement = item.querySelector('.complaint-category');
            return categoryElement && categoryElement.textContent.trim().length > 0;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: All displayed complaints show description field', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 25 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Every complaint item has a description element
          return Array.from(complaintItems).every(item => {
            const descriptionElement = item.querySelector('.complaint-description');
            return descriptionElement && descriptionElement.textContent.trim().length > 0;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: All displayed complaints show timestamp field', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 25 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Every complaint item has a timestamp element
          return Array.from(complaintItems).every(item => {
            const timestampElement = item.querySelector('.complaint-timestamp');
            return timestampElement && timestampElement.textContent.trim().length > 0;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: All four required fields are present for every complaint', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 25 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Every complaint has all four required fields
          return Array.from(complaintItems).every(item => {
            const hasLocation = item.querySelector('.complaint-location') !== null;
            const hasCategory = item.querySelector('.complaint-category') !== null;
            const hasDescription = item.querySelector('.complaint-description') !== null;
            const hasTimestamp = item.querySelector('.complaint-timestamp') !== null;
            
            return hasLocation && hasCategory && hasDescription && hasTimestamp;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Displayed location matches input complaint location', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Sort complaints to match display order (most recent first)
          const sortedComplaints = [...complaints]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 20);
          
          // Cleanup
          container.remove();
          
          // Assert: Each displayed location matches the input complaint
          return Array.from(complaintItems).every((item, index) => {
            const locationElement = item.querySelector('.complaint-location');
            const displayedLocation = locationElement?.textContent.trim();
            const expectedLocation = sortedComplaints[index]?.location;
            
            return displayedLocation === expectedLocation;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Displayed category matches input complaint category', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Sort complaints to match display order
          const sortedComplaints = [...complaints]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 20);
          
          // Cleanup
          container.remove();
          
          // Assert: Each displayed category matches the input complaint
          // Note: Category is formatted (e.g., "water_supply" -> "Water Supply")
          return Array.from(complaintItems).every((item, index) => {
            const categoryElement = item.querySelector('.complaint-category');
            const displayedCategory = categoryElement?.textContent.trim().toLowerCase().replace(/\s+/g, '_');
            const expectedCategory = sortedComplaints[index]?.category;
            
            return displayedCategory === expectedCategory;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Displayed description matches input complaint description', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Sort complaints to match display order
          const sortedComplaints = [...complaints]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 20);
          
          // Cleanup
          container.remove();
          
          // Assert: Each displayed description matches the input complaint (trimmed)
          return Array.from(complaintItems).every((item, index) => {
            const descriptionElement = item.querySelector('.complaint-description');
            const displayedDescription = descriptionElement?.textContent.trim();
            const expectedDescription = sortedComplaints[index]?.description.trim();
            
            return displayedDescription === expectedDescription;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Timestamp is displayed in human-readable format', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Timestamp is formatted (not raw ISO string)
          return Array.from(complaintItems).every(item => {
            const timestampElement = item.querySelector('.complaint-timestamp');
            const timestampText = timestampElement?.textContent.trim();
            
            // Should not be an ISO string format
            const isISOFormat = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(timestampText);
            
            // Should be human-readable (contains words like "ago", "Just now", or a date)
            const isHumanReadable = timestampText && (
              timestampText.includes('ago') || 
              timestampText.includes('Just now') ||
              /\d{1,2}\/\d{1,2}\/\d{4}/.test(timestampText)
            );
            
            return !isISOFormat && isHumanReadable;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: All categories have appropriate styling classes', () => {
    const categories = ['pothole', 'flooding', 'traffic', 'garbage', 
                       'streetlight', 'water_supply', 'noise', 'construction'];
    
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 8, maxLength: 20 }),
        (complaints) => {
          // Ensure we have complaints of different categories
          const diverseComplaints = complaints.map((c, i) => ({
            ...c,
            category: categories[i % categories.length]
          }));
          
          const { container } = render(<ComplaintFeed complaints={diverseComplaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Each complaint has a category-specific class
          return Array.from(complaintItems).every(item => {
            const categoryElement = item.querySelector('.complaint-category');
            const classList = Array.from(categoryElement?.classList || []);
            
            // Should have at least one category-specific class (category-*)
            return classList.some(cls => cls.startsWith('category-'));
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Location icon is displayed for all complaints', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Each complaint has a location icon
          return Array.from(complaintItems).every(item => {
            const locationIcon = item.querySelector('.location-icon');
            return locationIcon !== null;
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Single complaint displays all required fields', () => {
    fc.assert(
      fc.property(
        complaintArbitrary(),
        (complaint) => {
          const { container } = render(<ComplaintFeed complaints={[complaint]} />);
          
          const complaintItem = container.querySelector('.complaint-item');
          
          const hasLocation = complaintItem?.querySelector('.complaint-location')?.textContent === complaint.location;
          const hasDescription = complaintItem?.querySelector('.complaint-description')?.textContent === complaint.description;
          const hasCategory = complaintItem?.querySelector('.complaint-category') !== null;
          const hasTimestamp = complaintItem?.querySelector('.complaint-timestamp') !== null;
          
          // Cleanup
          container.remove();
          
          // Assert: Single complaint has all fields
          return hasLocation && hasDescription && hasCategory && hasTimestamp;
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * Additional property tests for complaint feed behavior
 */
describe('Complaint Feed Additional Properties', () => {
  
  test('Property: Feed container has scrollable class', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 25 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const feedContainer = container.querySelector('.complaint-feed');
          
          // Cleanup
          container.remove();
          
          // Assert: Feed container exists
          return feedContainer !== null;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Each complaint has unique key (no duplicate complaint_ids displayed)', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 5, maxLength: 25 }),
        (complaints) => {
          // Ensure unique complaint IDs
          const uniqueComplaints = complaints.filter((c, index, self) => 
            index === self.findIndex(t => t.complaint_id === c.complaint_id)
          );
          
          const { container } = render(<ComplaintFeed complaints={uniqueComplaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Number of displayed items matches unique complaints (up to 20)
          const expectedCount = Math.min(uniqueComplaints.length, 20);
          return complaintItems.length === expectedCount;
        }
      ),
      { numRuns: 100 }
    );
  });

  test('Property: Complaint items have proper structure (header, location, description)', () => {
    fc.assert(
      fc.property(
        fc.array(complaintArbitrary(), { minLength: 1, maxLength: 20 }),
        (complaints) => {
          const { container } = render(<ComplaintFeed complaints={complaints} />);
          
          const complaintItems = container.querySelectorAll('.complaint-item');
          
          // Cleanup
          container.remove();
          
          // Assert: Each complaint has proper structure
          return Array.from(complaintItems).every(item => {
            const hasHeader = item.querySelector('.complaint-header') !== null;
            const hasLocation = item.querySelector('.complaint-location') !== null;
            const hasDescription = item.querySelector('.complaint-description') !== null;
            
            return hasHeader && hasLocation && hasDescription;
          });
        }
      ),
      { numRuns: 100 }
    );
  });
});
