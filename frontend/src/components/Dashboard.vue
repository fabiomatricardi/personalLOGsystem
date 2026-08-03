<script setup>
import { ref, onMounted } from 'vue'
import { fetchDashboardStats } from '../composables/useApi.js'

const stats = ref(null)
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    stats.value = await fetchDashboardStats()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Dashboard</h2>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-banner">{{ error }}</div>
    <template v-else-if="stats">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_entries }}</div>
          <div class="stat-label">Total Entries</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_logs }}</div>
          <div class="stat-label">Logs</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_todos }}</div>
          <div class="stat-label">TODOs</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_tasks }}</div>
          <div class="stat-label">Tasks</div>
        </div>
      </div>

      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-value" style="color: var(--text-secondary)">{{ stats.pending_tasks }}</div>
          <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--accent)">{{ stats.assigned_tasks }}</div>
          <div class="stat-label">Assigned</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--warning)">{{ stats.ongoing_tasks }}</div>
          <div class="stat-label">Ongoing</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--success)">{{ stats.completed_tasks }}</div>
          <div class="stat-label">Completed</div>
        </div>
      </div>

      <div v-if="stats.overdue_tasks > 0" class="card" style="border-color: var(--error)">
        <div class="card-header">
          <span style="color: var(--error); font-weight: 600">
            <i class="pi pi-exclamation-triangle"></i> Overdue Tasks
          </span>
          <span class="stat-value" style="color: var(--error)">{{ stats.overdue_tasks }}</span>
        </div>
        <p style="color: var(--text-secondary)">You have tasks past their due date. Check the Analysis tab for recommendations.</p>
      </div>
    </template>
  </div>
</template>
