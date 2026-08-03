<script setup>
import { ref, onMounted } from 'vue'
import { generateAnalysis, fetchReports, deleteReport, deleteAllReports } from '../composables/useApi.js'
import { marked } from 'marked'

const reports = ref([])
const currentReport = ref(null)
const loading = ref(false)
const error = ref(null)
const success = ref('')
const reportType = ref('weekly')
const availableWeeks = ref([])

// Week selection
const selectedYear = ref(new Date().getFullYear())
const selectedWeek = ref(getCurrentWeek())

function getCurrentWeek() {
  const now = new Date()
  const jan4 = new Date(now.getFullYear(), 0, 4)
  const startOfWeek1 = new Date(jan4.getTime() - (jan4.getDay() % 7) * 86400000)
  const weekNum = Math.ceil(((now - startOfWeek1) / 86400000 + 1) / 7)
  return weekNum
}

const reportTypes = [
  { value: 'weekly', label: 'Weekly Summary', description: 'Summary for a specific week' },
  { value: 'comprehensive', label: 'Comprehensive Report', description: 'Full report covering all data' },
  { value: 'overdue', label: 'Overdue Tasks', description: 'Analysis of overdue items' },
  { value: 'next_steps', label: 'Next Steps', description: 'AI-suggested priorities' },
  { value: 'patterns', label: 'Pattern Analysis', description: 'Work pattern insights' }
]

const loadReports = async () => {
  try {
    reports.value = await fetchReports()
  } catch (e) {
    error.value = e.message
  }
}

const loadAvailableWeeks = async () => {
  try {
    const response = await fetch('/api/analysis/weeks')
    availableWeeks.value = await response.json()
  } catch (e) {
    console.error('Failed to load weeks:', e)
  }
}

onMounted(() => {
  loadReports()
  loadAvailableWeeks()
})

const generate = async () => {
  loading.value = true
  error.value = null
  success.value = ''
  try {
    const request = { report_type: reportType.value }

    if (reportType.value === 'weekly') {
      request.year = selectedYear.value
      request.week_number = selectedWeek.value
    }

    const result = await generateAnalysis(request)
    currentReport.value = result
    success.value = 'Report generated successfully!'
    loadReports()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

const viewReport = (report) => {
  currentReport.value = report
  error.value = null
  success.value = ''
}

const downloadReport = async (reportId) => {
  try {
    const response = await fetch(`/api/analysis/reports/${reportId}/download`)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'report.md'
    a.click()
    window.URL.revokeObjectURL(url)
    success.value = 'Report downloaded!'
  } catch (e) {
    error.value = e.message
  }
}

const downloadAllReports = async () => {
  try {
    const response = await fetch('/api/analysis/reports/download-all')
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'all_reports.md'
    a.click()
    window.URL.revokeObjectURL(url)
    success.value = 'All reports downloaded!'
  } catch (e) {
    error.value = e.message
  }
}

const handleDeleteReport = async (reportId) => {
  if (!confirm('Delete this report?')) return
  try {
    await deleteReport(reportId)
    if (currentReport.value?.id === reportId) {
      currentReport.value = null
    }
    loadReports()
    success.value = 'Report deleted'
  } catch (e) {
    error.value = e.message
  }
}

const handleDeleteAllReports = async () => {
  if (!confirm('Delete ALL reports? This cannot be undone.')) return
  try {
    await deleteAllReports()
    currentReport.value = null
    loadReports()
    success.value = 'All reports deleted'
  } catch (e) {
    error.value = e.message
  }
}

const renderMarkdown = (content) => {
  return marked(content || '')
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Analysis & Reports</h2>
      <div style="display: flex; gap: 8px">
        <button class="btn-secondary" @click="downloadAllReports" :disabled="reports.length === 0">
          <i class="pi pi-download"></i> Download All
        </button>
        <button class="btn-danger" @click="handleDeleteAllReports" :disabled="reports.length === 0" style="padding: 10px 16px">
          <i class="pi pi-trash"></i> Clear All
        </button>
      </div>
    </div>

    <div v-if="success" class="success-banner">{{ success }}</div>
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="card" style="margin-bottom: 20px">
      <div style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap">
        <div class="form-group" style="margin-bottom: 0; min-width: 200px">
          <label class="form-label">Report Type</label>
          <select v-model="reportType" class="form-select">
            <option v-for="rt in reportTypes" :key="rt.value" :value="rt.value">
              {{ rt.label }}
            </option>
          </select>
          <small style="color: var(--text-secondary); font-size: 0.75rem">
            {{ reportTypes.find(r => r.value === reportType)?.description }}
          </small>
        </div>

        <div v-if="reportType === 'weekly'" style="display: flex; gap: 12px">
          <div class="form-group" style="margin-bottom: 0; min-width: 100px">
            <label class="form-label">Year</label>
            <select v-model="selectedYear" class="form-select">
              <option :value="new Date().getFullYear()">{{ new Date().getFullYear() }}</option>
              <option :value="new Date().getFullYear() - 1">{{ new Date().getFullYear() - 1 }}</option>
            </select>
          </div>

          <div class="form-group" style="margin-bottom: 0; min-width: 100px">
            <label class="form-label">Week #</label>
            <select v-model="selectedWeek" class="form-select">
              <option v-for="w in 52" :key="w" :value="w">Week {{ w }}</option>
            </select>
          </div>
        </div>

        <button class="btn-primary" @click="generate" :disabled="loading" style="height: fit-content">
          {{ loading ? 'Generating...' : 'Generate Report' }}
        </button>
      </div>

      <div v-if="availableWeeks.length > 0 && reportType === 'weekly'" style="margin-top: 16px">
        <label class="form-label">Available weeks with data:</label>
        <div style="display: flex; gap: 8px; flex-wrap: wrap">
          <button
            v-for="week in availableWeeks.slice(0, 10)"
            :key="`${week.year}-${week.week}`"
            class="chip"
            :class="{ active: selectedYear === week.year && selectedWeek === week.week }"
            @click="selectedYear = week.year; selectedWeek = week.week"
          >
            W{{ week.week }} {{ week.year }} ({{ week.count }})
          </button>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 300px 1fr; gap: 20px">
      <div class="card" style="max-height: 600px; overflow-y: auto">
        <h3 style="margin-bottom: 16px">Recent Reports</h3>
        <div v-if="reports.length === 0" style="color: var(--text-secondary); padding: 20px; text-align: center">
          No reports generated yet
        </div>
        <div
          v-for="report in reports"
          :key="report.id"
          class="entry-item"
          style="margin-bottom: 8px"
          @click="viewReport(report)"
        >
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span style="font-size: 0.875rem; font-weight: 500; text-transform: capitalize">
              {{ report.report_type }}
            </span>
            <div style="display: flex; gap: 4px">
              <button
                class="btn-secondary"
                style="padding: 4px 8px; font-size: 0.75rem"
                @click.stop="downloadReport(report.id)"
                title="Download as Markdown"
              >
                <i class="pi pi-download"></i>
              </button>
              <button
                class="btn-secondary"
                style="padding: 4px 8px; font-size: 0.75rem; color: var(--error)"
                @click.stop="handleDeleteReport(report.id)"
                title="Delete report"
              >
                <i class="pi pi-trash"></i>
              </button>
            </div>
          </div>
          <div v-if="report.period_start" style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px">
            {{ report.period_start }} to {{ report.period_end }}
          </div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px">
            {{ formatDate(report.generated_at) }}
          </div>
        </div>
      </div>

      <div class="card">
        <div v-if="loading" class="loading">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
          <p style="margin-top: 16px">Generating report with AI...</p>
        </div>
        <div v-else-if="currentReport">
          <div style="display: flex; justify-content: flex-end; margin-bottom: 16px">
            <button
              v-if="currentReport.id"
              class="btn-secondary"
              @click="downloadReport(currentReport.id)"
            >
              <i class="pi pi-download"></i> Download Markdown
            </button>
          </div>
          <div class="markdown-content" v-html="renderMarkdown(currentReport.content)"></div>
        </div>
        <div v-else class="empty-state">
          <i class="pi pi-chart-bar" style="font-size: 3rem; opacity: 0.5"></i>
          <p style="margin-top: 16px">Select a report type and click Generate</p>
          <p style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 8px">
            Configure your LLM API in Settings first
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
