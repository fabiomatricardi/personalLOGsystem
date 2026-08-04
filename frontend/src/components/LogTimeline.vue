<script setup>
import { ref, onMounted } from 'vue'
import { fetchEntries, fetchEntry, updateEntry, deleteEntry } from '../composables/useApi.js'

const entries = ref([])
const loading = ref(true)
const error = ref(null)
const search = ref('')
const typeFilter = ref('')

const showModal = ref(false)
const editForm = ref({
  id: null,
  activity: '',
  type: 'LOG',
  status: '',
  follow_up: '',
  eta: ''
})
const saving = ref(false)

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

const openEditModal = async (entry) => {
  try {
    const fresh = await fetchEntry(entry.id)
    editForm.value = {
      id: fresh.id,
      activity: fresh.activity || '',
      type: fresh.type || 'LOG',
      status: fresh.status || '',
      follow_up: fresh.follow_up || '',
      eta: fresh.eta ? fresh.eta.slice(0, 16) : ''
    }
    showModal.value = true
  } catch (e) {
    error.value = 'Failed to load entry: ' + e.message
  }
}

const closeModal = () => {
  showModal.value = false
  editForm.value = { id: null, activity: '', type: 'LOG', status: '', follow_up: '', eta: '' }
}

const saveEntry = async () => {
  if (!editForm.value.activity.trim()) {
    error.value = 'Activity is required'
    return
  }
  saving.value = true
  try {
    await updateEntry(editForm.value.id, {
      activity: editForm.value.activity,
      type: editForm.value.type,
      status: editForm.value.status || null,
      follow_up: editForm.value.follow_up || null,
      eta: editForm.value.eta || null
    })
    closeModal()
    await loadEntries()
  } catch (e) {
    error.value = 'Failed to save: ' + e.message
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id) => {
  if (confirm('Are you sure you want to delete this entry?')) {
    try {
      await deleteEntry(id)
      closeModal()
      await loadEntries()
    } catch (e) {
      error.value = 'Failed to delete: ' + e.message
    }
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
      <div v-for="entry in entries" :key="entry.id" class="entry-item" @click="openEditModal(entry)">
        <div class="entry-meta">
          <span class="entry-type" :class="entry.type.toLowerCase()">{{ entry.type }}</span>
          <span class="entry-status" :class="(entry.status || '').toLowerCase()">{{ entry.status || 'No status' }}</span>
          <span>#{{ entry.id }}</span>
          <span>{{ formatDate(entry.timestamp) }}</span>
          <span v-if="entry.eta">ETA: {{ formatDate(entry.eta) }}</span>
          <span style="margin-left: auto; display: flex; gap: 4px">
            <button class="btn-icon" @click.stop="openEditModal(entry)" title="Edit">✏️</button>
            <button class="btn-icon btn-icon-danger" @click.stop="handleDelete(entry.id)" title="Delete">🗑️</button>
          </span>
        </div>
        <div class="entry-activity">{{ entry.activity }}</div>
        <div v-if="entry.follow_up" style="margin-top: 8px; color: var(--text-secondary); font-size: 0.875rem">
          Follow up: {{ entry.follow_up }}
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal">
          <h3 style="margin: 0 0 20px 0">Edit Entry #{{ editForm.id }}</h3>

          <div class="form-group">
            <label class="form-label">Activity *</label>
            <textarea v-model="editForm.activity" class="form-input" rows="3" placeholder="Describe the activity..."></textarea>
          </div>

          <div style="display: flex; gap: 12px">
            <div class="form-group" style="flex: 1">
              <label class="form-label">Type</label>
              <select v-model="editForm.type" class="form-select">
                <option value="LOG">LOG</option>
                <option value="TODO">TODO</option>
                <option value="TASK">TASK</option>
              </select>
            </div>
            <div class="form-group" style="flex: 1">
              <label class="form-label">Status</label>
              <select v-model="editForm.status" class="form-select">
                <option value="">None</option>
                <option value="PENDING">PENDING</option>
                <option value="ASSIGNED">ASSIGNED</option>
                <option value="ONGOING">ONGOING</option>
                <option value="COMPLETED">COMPLETED</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">ETA</label>
            <input type="datetime-local" v-model="editForm.eta" class="form-input" />
          </div>

          <div class="form-group">
            <label class="form-label">Follow up</label>
            <textarea v-model="editForm.follow_up" class="form-input" rows="2" placeholder="Follow-up notes..."></textarea>
          </div>

          <div class="modal-actions">
            <button class="btn-danger" @click="handleDelete(editForm.id)">Delete</button>
            <div style="display: flex; gap: 8px">
              <button class="btn-secondary" @click="closeModal">Cancel</button>
              <button class="btn-primary" @click="saveEntry" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
