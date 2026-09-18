import axios from 'axios'

const api = axios.create({
  baseURL: '',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function login(email, password) {
  const { data } = await api.post('/api/auth/login', { email, password })
  return data
}

export async function getMe() {
  const { data } = await api.get('/api/auth/me')
  return data
}

export async function getDashboard() {
  const { data } = await api.get('/api/dashboard')
  return data
}

export async function listBatches() {
  const { data } = await api.get('/api/batches')
  return data
}

export async function getBatch(id) {
  const { data } = await api.get(`/api/batches/${id}`)
  return data
}

export async function getBatchProgress(id) {
  const { data } = await api.get(`/api/batches/${id}/progress`)
  return data
}

export async function uploadFilesBatch(formData, onUploadProgress) {
  const { data } = await api.post('/api/batches/upload-files', formData, {
    onUploadProgress,
    timeout: 0,
  })
  return data
}

export async function uploadFolderBatch(formData, onUploadProgress) {
  const { data } = await api.post('/api/batches/upload-folder', formData, {
    onUploadProgress,
    timeout: 0,
  })
  return data
}

export async function uploadArchiveBatch(formData, onUploadProgress) {
  const { data } = await api.post('/api/batches/upload-archive', formData, {
    onUploadProgress,
    timeout: 0,
  })
  return data
}

export async function getBatchEntities(id) {
  const { data } = await api.get(`/api/batches/${id}/entities`)
  return data
}

export async function getEntityFiles(batchId, text, label) {
  const { data } = await api.get(`/api/batches/${batchId}/entity-files`, {
    params: { text, label },
  })
  return data
}

export async function getBatchComparison(batchId, refreshOpenAI = false) {
  const { data } = await api.get(`/api/batches/${batchId}/comparison`, {
    params: { refresh_openai: refreshOpenAI },
    timeout: 0,
  })
  return data
}

export async function getHistory() {
  const { data } = await api.get('/api/history')
  return data
}

export async function listUsers() {
  const { data } = await api.get('/api/auth/users')
  return data
}

export async function approveUser(id) {
  const { data } = await api.post(`/api/auth/users/${id}/approve`)
  return data
}

export async function getOpenAISettings() {
  const { data } = await api.get('/api/settings/openai')
  return data
}

export async function saveOpenAISettings(payload) {
  const { data } = await api.post('/api/settings/openai', payload)
  return data
}

export async function clearOpenAISettings() {
  const { data } = await api.delete('/api/settings/openai')
  return data
}

export default api
