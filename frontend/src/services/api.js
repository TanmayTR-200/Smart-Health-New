import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// PHC endpoints
export const getPHCs = () => api.get('/phcs');
export const getPHC = (id) => api.get(`/phcs/${id}`);

// Medicine endpoints
export const getMedicines = () => api.get('/medicines');
export const getMedicine = (id) => api.get(`/medicines/${id}`);

// Stock endpoints
export const getStock = (params) => api.get('/stock', { params });
export const getLowStock = () => api.get('/stock/low');

// Footfall endpoints
export const getFootfall = (params) => api.get('/footfall', { params });
export const getFootfallSummary = () => api.get('/footfall/summary');

// Bed occupancy endpoints
export const getBedOccupancy = (params) => api.get('/beds', { params });
export const getAvailableBeds = () => api.get('/beds/available');

// Attendance endpoints
export const getAttendance = (params) => api.get('/attendance', { params });
export const getAttendanceSummary = () => api.get('/attendance/summary');

// Test availability endpoints
export const getTestAvailability = (params) => api.get('/tests', { params });
export const getTestAvailabilitySummary = () => api.get('/tests/summary');

// ML Prediction endpoints
export const getStockoutPredictions = (params) => api.get('/predictions/stockouts', { params });
export const getDemandForecasts = (params) => api.get('/predictions/demand', { params });
export const getAnomalies = () => api.get('/anomalies');
export const getRedistributionRecommendations = () => api.get('/recommendations/redistribute');
export const executeRedistribution = () => api.post('/recommendations/redistribute/execute');

// Simulation endpoints
export const advanceSimulationDay = (data) => api.post('/simulation/advance-day', data);
export const triggerSimulationEvent = (data) => api.post('/simulation/trigger-event', data);
export const getSimulationStatus = () => api.get('/simulation/status');

// Dashboard endpoints
export const getDashboardSummary = () => api.get('/dashboard/summary');
export const getAlerts = () => api.get('/alerts');

// Translation endpoint
export const translateText = (text, language) => api.post('/translate', { text, language });

export default api;
