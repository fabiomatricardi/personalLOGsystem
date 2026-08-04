<script setup>
import { ref, onMounted } from 'vue'
import { fetchSettings, updateSettings, importExcel, exportExcel, backupDatabase, restoreDatabase, fetchDatabaseInfo, shutdownApp } from '../composables/useApi.js'

const settings = ref({
  app: { name: 'Personal Log Manager', version: '1.0.0', port: 8000, data_dir: './data', db_path: './data/personal_log.db', log_level: 'INFO' },
  llm: {
    primary: { base_url: '', api_key: '', model: '' },
    fallback: { base_url: '', api_key: '', model: '' },
    analysis: { weekly_report_day: 'friday', auto_analyze: false, include_completed_tasks: true, summary_style: 'concise' }
  },
  ui: { theme: 'dark', sidebar_collapsed: false, date_format: 'YYYY-MM-DD HH:mm', items_per_page: 25 },
  import: { excel_path: '', last_import_date: null, auto_import_on_start: false }
})
const dbInfo = ref(null)
const loading = ref(false)
const error = ref(null)
const success = ref('')
const llmTestResult = ref(null)
const llmTesting = ref(false)
const originalPort = ref(8000)

const DEFAULT_SETTINGS = {
  app: { name: 'Personal Log Manager', version: '1.0.0', port: 8000, data_dir: './data', db_path: './data/personal_log.db', log_level: 'INFO' },
  llm: {
    primary: { base_url: '', api_key: '', model: '' },
    fallback: { base_url: '', api_key: '', model: '' },
    analysis: { weekly_report_day: 'friday', auto_analyze: false, include_completed_tasks: true, summary_style: 'concise' }
  },
  ui: { theme: 'dark', sidebar_collapsed: false, date_format: 'YYYY-MM-DD HH:mm', items_per_page: 25 },
  import: { excel_path: '', last_import_date: null, auto_import_on_start: false }
}

onMounted(async () => {
  try {
    const data = await fetchSettings()
    settings.value = {
      ...DEFAULT_SETTINGS,
      ...data,
      app: {
        ...DEFAULT_SETTINGS.app,
        ...(data.app || {})
      },
      llm: {
        ...DEFAULT_SETTINGS.llm,
        ...(data.llm || {}),
        primary: { ...DEFAULT_SETTINGS.llm.primary, ...(data.llm?.primary || {}) },
        fallback: { ...DEFAULT_SETTINGS.llm.fallback, ...(data.llm?.fallback || {}) },
        analysis: { ...DEFAULT_SETTINGS.llm.analysis, ...(data.llm?.analysis || {}) }
      }
    }
    originalPort.value = settings.value.app.port
  } catch (e) {
    settings.value = DEFAULT_SETTINGS
    error.value = 'Failed to load settings: ' + e.message
  }
  try {
    dbInfo.value = await fetchDatabaseInfo()
  } catch (e) {
    console.error('Failed to load database info:', e)
  }
})

const saveSettings = async () => {
  if (settings.value.app.port < 1024) {
    error.value = 'Port must be 1024 or higher (ports below 1024 require admin privileges)'
    return
  }

  loading.value = true
  error.value = null
  const portChanged = settings.value.app.port !== originalPort.value
  try {
    await updateSettings(settings.value)
    success.value = 'Settings saved successfully'
    if (portChanged) {
      if (confirm('Port changed. The application needs to restart. Restart now?')) {
        await shutdownApp()
        success.value = 'Application shut down. Please relaunch the executable.'
      } else {
        success.value = 'Settings saved. Port will take effect on next restart.'
      }
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const testLlmConnection = async () => {
  llmTesting.value = true
  llmTestResult.value = null
  error.value = null
  try {
    const response = await fetch('/api/analysis/test-llm')
    llmTestResult.value = await response.json()
  } catch (e) {
    llmTestResult.value = { status: 'error', message: e.message }
  } finally {
    llmTesting.value = false
  }
}

const handleImportExcel = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  loading.value = true
  error.value = null
  try {
    const result = await importExcel(file)
    success.value = `Imported ${result.imported} entries`
    dbInfo.value = await fetchDatabaseInfo()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const handleExportExcel = async () => {
  loading.value = true
  try {
    const blob = await exportExcel()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'personal_log_export.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
    success.value = 'Export downloaded'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const handleBackup = async () => {
  loading.value = true
  try {
    const blob = await backupDatabase()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `personal_log_backup.db`
    a.click()
    window.URL.revokeObjectURL(url)
    success.value = 'Backup downloaded'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const handleRestore = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  if (!confirm('This will replace the current database. Continue?')) return

  loading.value = true
  error.value = null
  try {
    const result = await restoreDatabase(file)
    success.value = result.message
    dbInfo.value = await fetchDatabaseInfo()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const handleShutdown = async () => {
  if (confirm('Are you sure you want to shut down the application?')) {
    await shutdownApp()
  }
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Settings</h2>
    </div>

    <div v-if="success" class="success-banner">{{ success }}</div>
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="card">
      <h3 style="margin-bottom: 16px">Database</h3>
      <div v-if="dbInfo && dbInfo.exists" style="margin-bottom: 16px; color: var(--text-secondary)">
        <p>Entries: {{ dbInfo.entry_count }} | Size: {{ dbInfo.size_mb }} MB</p>
      </div>

      <div style="display: flex; gap: 12px; flex-wrap: wrap">
        <div>
          <label class="btn-secondary" style="cursor: pointer">
            Import Excel
            <input type="file" accept=".xlsx,.xls" @change="handleImportExcel" style="display: none" />
          </label>
        </div>
        <button class="btn-secondary" @click="handleExportExcel" :disabled="loading">
          Export Excel
        </button>
        <button class="btn-primary" @click="handleBackup" :disabled="loading">
          Backup Database
        </button>
        <div>
          <label class="btn-danger" style="cursor: pointer">
            Restore Database
            <input type="file" accept=".db" @change="handleRestore" style="display: none" />
          </label>
        </div>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-bottom: 16px">Application</h3>
      <div class="form-group">
        <label class="form-label">Server Port</label>
        <input v-model.number="settings.app.port" class="form-input" type="number" min="1024" max="65535" />
        <small style="color: var(--text-secondary); margin-top: 4px; display: block;">
          Port for the backend server. Requires restart to take effect.
        </small>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-bottom: 16px">LLM Configuration</h3>

      <h4 style="margin-bottom: 12px; color: var(--text-secondary)">Primary API</h4>
      <div class="form-group">
        <label class="form-label">Base URL</label>
        <input v-model="settings.llm.primary.base_url" class="form-input" />
      </div>
      <div class="form-group">
        <label class="form-label">API Key</label>
        <input v-model="settings.llm.primary.api_key" class="form-input" type="password" />
      </div>
      <div class="form-group">
        <label class="form-label">Model</label>
        <input v-model="settings.llm.primary.model" class="form-input" />
      </div>

      <h4 style="margin: 20px 0 12px; color: var(--text-secondary)">Fallback API</h4>
      <div class="form-group">
        <label class="form-label">Base URL</label>
        <input v-model="settings.llm.fallback.base_url" class="form-input" />
      </div>
      <div class="form-group">
        <label class="form-label">API Key</label>
        <input v-model="settings.llm.fallback.api_key" class="form-input" type="password" />
      </div>
      <div class="form-group">
        <label class="form-label">Model</label>
        <input v-model="settings.llm.fallback.model" class="form-input" />
      </div>

      <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border)">
        <button class="btn-secondary" @click="testLlmConnection" :disabled="llmTesting">
          {{ llmTesting ? 'Testing...' : 'Test LLM Connection' }}
        </button>
        <div v-if="llmTestResult" style="margin-top: 12px; padding: 12px; border-radius: 8px;"
             :style="{ background: llmTestResult.status === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)' }">
          <strong v-if="llmTestResult.status === 'success'" style="color: var(--success)">Connected!</strong>
          <strong v-else style="color: var(--error)">Failed</strong>
          <p style="margin-top: 4px; font-size: 0.875rem; color: var(--text-secondary)">
            {{ llmTestResult.response || llmTestResult.message }}
          </p>
        </div>
      </div>
    </div>

    <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px">
      <button class="btn-danger" @click="handleShutdown">
        Shutdown App
      </button>
      <button class="btn-primary" @click="saveSettings" :disabled="loading">
        {{ loading ? 'Saving...' : 'Save Settings' }}
      </button>
    </div>
  </div>
</template>
