/**
 * Smoke test: Dashboard renders without crashing given mocked API responses.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LanguageProvider } from '../contexts/LanguageContext';

// Mock the API service
vi.mock('../services/api', () => ({
  getDashboardSummary: vi.fn(() => Promise.resolve({
    data: {
      total_phcs: 6,
      total_patients_today: 450,
      total_stockouts: 3,
      avg_attendance_rate: 82.5,
      avg_health_score: 88.0,
      avg_bed_occupancy: 78.5,
      critical_alerts: 2,
      warning_alerts: 4,
      simulated_date: '2024-12-31',
      phc_health_scores: [
        { phc_id: 1, phc_name: 'PHC-Rampura', phc_code: 'PHC001', health_score: 92.5, status: 'good', stock_health: 95, attendance_rate: 90, bed_occupancy_rate: 85, footfall_trend: 'stable' },
        { phc_id: 2, phc_name: 'PHC-Krishnanagar', phc_code: 'PHC002', health_score: 85.0, status: 'warning', stock_health: 80, attendance_rate: 78, bed_occupancy_rate: 90, footfall_trend: 'increasing' },
      ],
    }
  })),
  getAlerts: vi.fn(() => Promise.resolve({ data: [] })),
  getPHCs: vi.fn(() => Promise.resolve({ data: [] })),
}));

// Import after mock is set up
import Dashboard from '../pages/Dashboard';

function renderDashboard() {
  return render(
    <MemoryRouter>
      <LanguageProvider>
        <Dashboard />
      </LanguageProvider>
    </MemoryRouter>
  );
}

describe('Dashboard smoke test', () => {
  it('renders without crashing', async () => {
    const { container } = renderDashboard();
    await waitFor(() => {
      expect(screen.getByText('Total PHCs')).toBeInTheDocument();
    });
    expect(container).toBeTruthy();
  });

  it('shows the correct PHC count', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText('6')).toBeInTheDocument();
    });
  });

  it('shows PHC names from the API', async () => {
    renderDashboard();
    await waitFor(() => {
      expect(screen.getByText('PHC-Rampura')).toBeInTheDocument();
    });
  });
});
