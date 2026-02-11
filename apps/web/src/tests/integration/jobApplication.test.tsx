/**
 * Job Application Integration Tests
 * Microsoft-level comprehensive testing suite
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

// Mock components and hooks
import Dashboard from '../../pages/Dashboard';
import { useApplications } from '../../hooks/useApplications';

// Mock API responses
const mockJobs = [
  {
    id: 'job-1',
    title: 'Senior React Developer',
    company: 'TechCorp',
    salary_min: 120000,
    location: 'Remote',
    description: 'Looking for a senior React developer...',
  },
  {
    id: 'job-2',
    title: 'Frontend Engineer',
    company: 'StartupXYZ',
    salary_min: 100000,
    location: 'San Francisco, CA',
    description: 'Join our growing team...',
  },
];

const mockApplications = [
  {
    id: 'app-1',
    job_title: 'Senior React Developer',
    company: 'TechCorp',
    status: 'APPLIED',
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'app-2',
    job_title: 'Frontend Engineer',
    company: 'StartupXYZ',
    status: 'HOLD',
    hold_question: 'What is your experience with TypeScript?',
    created_at: '2024-01-14T15:30:00Z',
  },
];

// Test utilities
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
    },
    mutations: {
      retry: false,
    },
  },
});

const renderWithProviders = (ui: React.ReactElement, queryClient?: QueryClient) => {
  const client = queryClient || createTestQueryClient();

  return render(
    <QueryClientProvider client={client}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Mock API functions
const mockApiPost = vi.fn();
const mockApiGet = vi.fn();

vi.mock('../../lib/api', () => ({
  apiPost: mockApiPost,
  apiGet: mockApiGet,
}));

describe('Job Application Flow', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
    vi.clearAllMocks();

    // Setup default mock responses
    mockApiGet.mockResolvedValue(mockJobs);
    mockApiPost.mockResolvedValue({ success: true });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Job Discovery and Matching', () => {
    it('should display available jobs', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      // Check if jobs are loaded
      expect(mockApiGet).toHaveBeenCalledWith('jobs');
    });

    it('should filter jobs by location', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      const locationFilter = screen.getByPlaceholderText('Filter location...');
      fireEvent.change(locationFilter, { target: { value: 'Remote' } });

      await waitFor(() => {
        expect(mockApiGet).toHaveBeenCalledWith('jobs?location=Remote');
      });
    });

    it('should display job match scores', async () => {
      const jobsWithScores = mockJobs.map(job => ({
        ...job,
        match_score: {
          score: 0.85,
          skill_match: 0.9,
          experience_match: 0.8,
          location_match: 0.85,
          summary: 'Strong match for your profile',
        },
      }));

      mockApiGet.mockResolvedValue(jobsWithScores);

      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument();
      });
    });
  });

  describe('Job Swipe Actions', () => {
    it('should handle job acceptance', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      // Find and click accept button
      const acceptButton = screen.getByLabelText('Accept job');
      fireEvent.click(acceptButton);

      await waitFor(() => {
        expect(mockApiPost).toHaveBeenCalledWith('applications', {
          job_id: 'job-1',
          decision: 'ACCEPT',
        });
      });
    });

    it('should handle job rejection', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      // Find and click reject button
      const rejectButton = screen.getByLabelText('Reject job');
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(mockApiPost).toHaveBeenCalledWith('applications', {
          job_id: 'job-1',
          decision: 'REJECT',
        });
      });
    });

    it('should show optimistic UI updates', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      const acceptButton = screen.getByLabelText('Accept job');

      // Click accept
      fireEvent.click(acceptButton);

      // Check for optimistic update
      await waitFor(() => {
        expect(screen.getByText('Match queued! 🚀')).toBeInTheDocument();
      });
    });
  });

  describe('Application Management', () => {
    it('should display application status', async () => {
      mockApiGet.mockResolvedValue(mockApplications);

      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Transmissions')).toBeInTheDocument();
        expect(screen.getByText('APPLIED')).toBeInTheDocument();
        expect(screen.getByText('HOLD')).toBeInTheDocument();
      });
    });

    it('should handle hold questions', async () => {
      const applicationsWithHold = mockApplications.map(app =>
        app.status === 'HOLD' ? app : null
      ).filter(Boolean);

      mockApiGet.mockResolvedValue(applicationsWithHold);

      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('What is your experience with TypeScript?')).toBeInTheDocument();
      });
    });

    it('should submit hold answers', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Transmissions')).toBeInTheDocument();
      });

      // Find answer textarea and submit button
      const answerTextarea = screen.getByPlaceholderText('Type your response here...');
      const submitButton = screen.getByText('Submit Answer');

      fireEvent.change(answerTextarea, {
        target: { value: 'I have 5 years of experience with TypeScript.' }
      });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiPost).toHaveBeenCalledWith('applications/app-2/answer', {
          answer: 'I have 5 years of experience with TypeScript.',
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      mockApiPost.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      const acceptButton = screen.getByLabelText('Accept job');
      fireEvent.click(acceptButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to record decision')).toBeInTheDocument();
      });
    });

    it('should retry failed requests', async () => {
      mockApiPost
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ success: true });

      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      const acceptButton = screen.getByLabelText('Accept job');
      fireEvent.click(acceptButton);

      // Should show error
      await waitFor(() => {
        expect(screen.getByText('Failed to record decision')).toBeInTheDocument();
      });

      // Should retry and succeed
      await waitFor(() => {
        expect(screen.getByText('Match queued! 🚀')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Performance', () => {
    it('should load jobs within performance budget', async () => {
      const startTime = performance.now();

      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      const loadTime = performance.now() - startTime;
      expect(loadTime).toBeLessThan(2000); // 2 seconds budget
    });

    it('should handle large job lists efficiently', async () => {
      const largeJobList = Array.from({ length: 1000 }, (_, i) => ({
        id: `job-${i}`,
        title: `Job ${i}`,
        company: `Company ${i}`,
        salary_min: 80000 + (i * 1000),
        location: 'Remote',
        description: `Description for job ${i}`,
      }));

      mockApiGet.mockResolvedValue(largeJobList);

      const startTime = performance.now();
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      const renderTime = performance.now() - startTime;
      expect(renderTime).toBeLessThan(3000); // 3 seconds for large list
    });
  });

  describe('Accessibility', () => {
    it('should be keyboard navigable', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      // Test keyboard navigation
      const acceptButton = screen.getByLabelText('Accept job');
      acceptButton.focus();

      fireEvent.keyDown(acceptButton, { key: 'Enter' });

      await waitFor(() => {
        expect(mockApiPost).toHaveBeenCalled();
      });
    });

    it('should have proper ARIA labels', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      // Check for ARIA labels
      const acceptButton = screen.getByLabelText('Accept job');
      expect(acceptButton).toHaveAttribute('aria-label');
      expect(acceptButton).toHaveAttribute('role', 'button');
    });

    it('should support screen readers', async () => {
      renderWithProviders(<Dashboard />, queryClient);

      await waitFor(() => {
        expect(screen.getByText('Active Radar')).toBeInTheDocument();
      });

      // Check for proper semantic structure
      const mainContent = screen.getByRole('main');
      expect(mainContent).toBeInTheDocument();

      const jobCards = screen.getAllByRole('article');
      expect(jobCards.length).toBeGreaterThan(0);
    });
  });
});


describe('Security', () => {
  it('should sanitize user inputs', async () => {
    renderWithProviders(<Dashboard />, createTestQueryClient());

    await waitFor(() => {
      expect(screen.getByText('Active Radar')).toBeInTheDocument();
    });

    const locationFilter = screen.getByPlaceholderText('Filter location...');

    // Test XSS injection
    fireEvent.change(locationFilter, {
      target: { value: '<script>alert("xss")</script>' }
    });

    // Should sanitize input
    expect(locationFilter).not.toHaveValue('<script>alert("xss")</script>');
  });

  it('should validate API responses', async () => {
    const maliciousResponse = {
      id: 'job-1',
      title: '<script>alert("xss")</script>',
      company: 'EvilCorp',
      description: 'Click here for malware: <a href="javascript:alert(\'xss\')">Link</a>',
    };

    mockApiGet.mockResolvedValue([maliciousResponse]);

    renderWithProviders(<Dashboard />, createTestQueryClient());

    await waitFor(() => {
      expect(screen.queryByText('<script>alert("xss")</script>')).not.toBeInTheDocument();
      expect(screen.queryByText('Click here for malware:')).not.toBeInTheDocument();
    });
  });
});
