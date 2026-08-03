<script setup>
import { ref, onMounted } from 'vue'
import { fetchEntries, deleteEntry } from '../composables/useApi.js'

const entries = ref([])
const loading = ref(true)
const error = ref(null)
const search = ref('')
const typeFilter = ref('')

const loadEntries = async () => {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (typeFilter.value) params.type = typeFilter.value
    const result = await fetchEntries(params)
    entries.value = result.entries
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadEntries)

const handleDelete = async (id) => {
  if (confirm('Are you sure you want to delete this entry?')) {
    await deleteEntry(id)
    loadEntries()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Log Timeline</h2>
    </div>

    <div class="card" style="margin-bottom: 20px">
      <div style="display: flex; gap: 12px; align-items: center">
        <input
          v-model="search"
          class="form-input"
          placeholder="Search entries..."
          @input="loadEntries"
          style="flex: 1"
        />
        <select v-model="typeFilter" class="form-select" style="width: 150px" @change="loadEntries">
          <option value="">All Types</option>
          <option value="LOG">LOG</option>
          <option value="TODO">TODO</option>
          <option value="TASK">TASK</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-banner">{{ error }}</div>
    <div v-else-if="entries.length === 0" class="empty-state">
      <i class="pi pi-inbox"></i>
      <p>No entries found</p>
    </div>
    <div v-else class="entry-list">
      <div v-for="entry in entries" :key="entry.id" class="entry-item">
        <div class="entry-meta">
          <span class="entry-type" :class="entry.type.toLowerCase()">{{ entry.type }}</span>
          <span class="entry-status" :class="(entry.status || '').toLowerCase()">{{ entry.status }}</span>
          <span>{{ formatDate(entry.timestamp) }}</span>
          <span v-if="entry.eta">ETA: {{ formatDate(entry.eta) }}</span>
        </div>
        <div class="entry-activity">{{ entry.activity }}</div>
        <div v-if="entry.follow_up" style="margin-top: 8px; color: var(--text-secondary); font-size: 0.875rem">
          Follow up: {{ entry.follow_up }}
        </div>
      </div>
    </div>
  </div>
</template>
