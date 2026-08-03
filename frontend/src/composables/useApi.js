import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export async function fetchEntries(params = {}) {
  const { data } = await api.get('/entries', { params })
  return data
}

export async function fetchEntry(id) {
  const { data } = await api.get(`/entries/${id}`)
  return data
}

export async function createEntry(entry) {
  const { data } = await api.post('/entries', entry)
  return data
}

export async function updateEntry(id, entry) {
  const { data } = await api.put(`/entries/${id}`, entry)
  return data
}

export async function deleteEntry(id) {
  const { data } = await api.delete(`/entries/${id}`)
  return data
}

export async function fetchDashboardStats() {
  const { data } = await api.get('/entries/stats/dashboard')
  return data
}

export async function fetchTags() {
  const { data } = await api.get('/tags')
  return data
}

export async function createTag(tag) {
  const { data } = await api.post('/tags', tag)
  return data
}

export async function deleteTag(id) {
  const { data } = await api.delete(`/tags/${id}`)
  return data
}

export async function generateAnalysis(request) {
  const { data } = await api.post('/analysis/generate', request)
  return data
}

export async function fetchReports(limit = 20) {
  const { data } = await api.get('/analysis/reports', { params: { limit } })
  return data
}

export async function fetchReport(id) {
  const { data } = await api.get(`/analysis/reports/${id}`)
  return data
}

export async function deleteReport(id) {
  const { data } = await api.delete(`/analysis/reports/${id}`)
  return data
}

export async function updateReport(id, reportData) {
  const { data } = await api.put(`/analysis/reports/${id}`, reportData)
  return data
}

export async function deleteAllReports() {
  const { data } = await api.delete('/analysis/reports')
  return data
}

export async function importExcel(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/data/import/excel', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

export async function exportExcel() {
  const response = await api.get('/data/export/excel', { responseType: 'blob' })
  return response.data
}

export async function backupDatabase() {
  const response = await api.post('/data/backup', {}, { responseType: 'blob' })
  return response.data
}

export async function restoreDatabase(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/data/restore', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}

export async function fetchDatabaseInfo() {
  const { data } = await api.get('/data/info')
  return data
}

export async function fetchSettings() {
  const { data } = await api.get('/settings')
  return data
}

export async function updateSettings(config) {
  const { data } = await api.post('/settings', config)
  return data
}

export async function shutdownApp() {
  await api.post('/shutdown')
}
