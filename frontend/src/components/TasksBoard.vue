<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchEntries, updateEntry } from '../composables/useApi.js'

const entries = ref([])
const loading = ref(true)
const error = ref(null)
const editingEntry = ref(null)

const columns = [
  { status: 'PENDING', label: 'Pending', color: 'var(--text-secondary)' },
  { status: 'ASSIGNED', label: 'Assigned', color: 'var(--accent)' },
  { status: 'ONGOING', label: 'Ongoing', color: 'var(--warning)' },
  { status: 'COMPLETED', label: 'Completed', color: 'var(--success)' }
]

const taskEntries = computed(() => entries.value.filter(e => e.type === 'TASK' || e.type === 'TODO'))

const getColumnEntries = (status) => {
  return taskEntries.value.filter(e => e.status === status)
}

const loadEntries = async () => {
  loading.value = true
  try {
    const result = await fetchEntries({ limit: 200 })
    entries.value = result.entries
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadEntries)

const moveToStatus = async (entryId, newStatus) => {
  await updateEntry(entryId, { status: newStatus })
  loadEntries()
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Tasks Board</h2>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-banner">{{ error }}</div>
    <div v-else class="kanban-board">
      <div v-for="col in columns" :key="col.status" class="kanban-column">
        <div class="kanban-column-header">
          <span :style="{ color: col.color }">{{ col.label }}</span>
          <span class="kanban-count">{{ getColumnEntries(col.status).length }}</span>
        </div>
        <div class="kanban-items">
          <div
            v-for="entry in getColumnEntries(col.status)"
            :key="entry.id"
            class="kanban-card"
          >
            <div class="entry-meta">
              <span class="entry-type" :class="entry.type.toLowerCase()">{{ entry.type }}</span>
              <span style="color: var(--text-secondary); font-size: 0.75rem">#{{ entry.id }}</span>
            </div>
            <div style="font-size: 0.875rem; margin: 8px 0">{{ entry.activity }}</div>
            <div v-if="entry.eta" style="font-size: 0.75rem; color: var(--text-secondary)">
              ETA: {{ formatDate(entry.eta) }}
            </div>
            <div style="margin-top: 8px; display: flex; gap: 4px; flex-wrap: wrap">
              <button
                v-for="nextStatus in columns.filter(c => c.status !== entry.status)"
                :key="nextStatus.status"
                class="btn-secondary"
                style="padding: 4px 8px; font-size: 0.75rem"
                @click="moveToStatus(entry.id, nextStatus.status)"
              >
                {{ nextStatus.label }}
              </button>
            </div>
          </div>
          <div v-if="getColumnEntries(col.status).length === 0" style="text-align: center; color: var(--text-secondary); padding: 20px">
            No items
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
