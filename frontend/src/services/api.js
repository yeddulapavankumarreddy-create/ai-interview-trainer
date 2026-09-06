import axios from 'axios'

// In development the Vite dev server proxies /api → http://localhost:8000,
// so we use a relative base URL.  This keeps all requests same-origin and
// avoids CORS preflights entirely during development.
// Set VITE_API_URL to an absolute URL only when deploying to a separate host.
const API_BASE = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred.'
    return Promise.reject(new Error(message))
  }
)

// ── Status ────────────────────────────────────────────────────────────────────
export const getStatus = () => api.get('/api/status').then((r) => r.data)

// ── Profile ───────────────────────────────────────────────────────────────────
export const getProfile = (profileId = 1) =>
  api.get(`/api/profile?profile_id=${profileId}`).then((r) => r.data)

export const saveProfile = (data) =>
  api.post('/api/profile', data).then((r) => r.data)

export const updateProfile = (profileId, data) =>
  api.put(`/api/profile/${profileId}`, data).then((r) => r.data)

// ── Resume ────────────────────────────────────────────────────────────────────
export const uploadResume = (file, profileId = 1) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('profile_id', profileId)
  return api
    .post('/api/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data)
}

export const getResume = (profileId = 1) =>
  api.get(`/api/resume/${profileId}`).then((r) => r.data)

// ── Interview ─────────────────────────────────────────────────────────────────
export const createInterview = (data) =>
  api.post('/api/interview/create', data).then((r) => r.data)

export const getInterview = (id) =>
  api.get(`/api/interview/${id}`).then((r) => r.data)

export const getQuestions = (interviewId) =>
  api.get(`/api/interview/${interviewId}/questions`).then((r) => r.data)

export const getRagSources = (interviewId) =>
  api.get(`/api/interview/${interviewId}/rag-sources`).then((r) => r.data)

export const submitAnswer = (interviewId, data) =>
  api.post(`/api/interview/${interviewId}/answer`, data).then((r) => r.data)

export const finishInterview = (interviewId) =>
  api.post(`/api/interview/${interviewId}/finish`).then((r) => r.data)

export const getReport = (interviewId) =>
  api.get(`/api/interview/${interviewId}/report`).then((r) => r.data)

export const listInterviews = (profileId = 1) =>
  api.get(`/api/interviews?profile_id=${profileId}`).then((r) => r.data)

// ── Analytics ─────────────────────────────────────────────────────────────────
export const getAnalytics = (profileId = 1) =>
  api.get(`/api/analytics?profile_id=${profileId}`).then((r) => r.data)

// ── Preparation ───────────────────────────────────────────────────────────────
export const getPreparationPlans = (profileId = 1) =>
  api.get(`/api/preparation?profile_id=${profileId}`).then((r) => r.data)

export const generatePreparationPlan = (profileId = 1, weakAreas = '') =>
  api
    .post(`/api/preparation/generate?profile_id=${profileId}&weak_areas=${encodeURIComponent(weakAreas)}`)
    .then((r) => r.data)

export default api
