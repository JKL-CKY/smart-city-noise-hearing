import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const recordingsAPI = {
  upload: (formData) => api.post('/recordings/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  list: (params) => api.get('/recordings', { params }),
  get: (id) => api.get(`/recordings/${id}`),
  getTranscription: (id) => api.get(`/recordings/${id}/transcription`),
  updateStatus: (id, status) => api.put(`/recordings/${id}/status?status=${status}`),
};

export const hearingsAPI = {
  create: (data) => api.post('/hearings', data),
  list: (params) => api.get('/hearings', { params }),
  get: (id) => api.get(`/hearings/${id}`),
  process: (id, referenceMicId = null) => {
    const url = referenceMicId
      ? `/hearings/${id}/process?reference_microphone_id=${referenceMicId}`
      : `/hearings/${id}/process`;
    return api.post(url);
  },
  addRecording: (hearingId, recordingId) =>
    api.post(`/hearings/${hearingId}/recordings/${recordingId}`),
  getReport: (id) => api.get(`/hearings/${id}/report`),
};

export const noiseMapAPI = {
  getHeatmap: (params) => api.get('/noise-map/heatmap', { params }),
  getDevices: (params) => api.get('/noise-map/devices', { params }),
  createDevice: (data) => api.post('/noise-map/devices', data),
  getReportPoints: (params) => api.get('/noise-map/report-points', { params }),
  createReportPoint: (data) => api.post('/noise-map/report-points', data),
  getReportPoint: (id) => api.get(`/noise-map/report-points/${id}`),
  updateReportPointStatus: (id, status) =>
    api.put(`/noise-map/report-points/${id}/status?status=${status}`),
  getDistrictStats: (params) => api.get('/noise-map/district-stats', { params }),
};

export const reportsAPI = {
  list: (params) => api.get('/reports', { params }),
  get: (id) => api.get(`/reports/${id}`),
  download: (id) => api.get(`/reports/${id}/download`, { responseType: 'blob' }),
  sendEmail: (id, target) =>
    api.post(`/reports/${id}/send-email?target=${target}`),
  getEmailStatus: (id) => api.get(`/reports/${id}/email-status`),
};

export default api;
