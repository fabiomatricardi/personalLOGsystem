<script setup>
import { ref, onMounted } from 'vue'
import { createEntry, fetchEntries } from '../composables/useApi.js'

const emit = defineEmits(['navigate'])

const form = ref({
  activity: '',
  type: 'LOG',
  follow_up: '',
  status: '',
  reference_id: null,
  eta: ''
})

const entries = ref([])
const success = ref(false)
const error = ref(null)
const loading = ref(false)

onMounted(async () => {
  const result = await fetchEntries({ limit: 50 })
  entries.value = result.entries
})

const handleSubmit = async () => {
  if (!form.value.activity.trim()) {
    error.value = 'Activity is required'
    return
  }

  loading.value = true
  error.value = null
  success.value = false

  try {
    const data = { ...form.value }
    if (!data.status) {
      data.status = data.type === 'LOG' ? 'LOG' : 'PENDING'
    }
    if (!data.reference_id) delete data.reference_id
    if (!data.eta) delete data.eta
    if (!data.follow_up) delete data.follow_up

    await createEntry(data)
    success.value = true
    form.value = { activity: '', type: 'LOG', follow_up: '', status: '', reference_id: null, eta: '' }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>New Entry</h2>
    </div>

    <div v-if="success" class="success-banner">Entry created successfully!</div>
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div class="card">
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">Type</label>
          <select v-model="form.type" class="form-select">
            <option value="LOG">LOG</option>
            <option value="TODO">TODO</option>
            <option value="TASK">TASK</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Activity *</label>
          <textarea
            v-model="form.activity"
            class="form-textarea"
            rows="5"
            placeholder="Describe the activity..."
            required
          ></textarea>
        </div>

        <div class="form-group">
          <label class="form-label">Follow Up</label>
          <input
            v-model="form.follow_up"
            class="form-input"
            placeholder="Who/what to follow up on"
          />
        </div>

        <div class="form-group" v-if="form.type !== 'LOG'">
          <label class="form-label">Status</label>
          <select v-model="form.status" class="form-select">
            <option value="">Auto</option>
            <option value="PENDING">Pending</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="ONGOING">Ongoing</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>

        <div class="form-group" v-if="form.type !== 'LOG'">
          <label class="form-label">ETA</label>
          <input
            v-model="form.eta"
            class="form-input"
            type="datetime-local"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Reference Entry</label>
          <select v-model="form.reference_id" class="form-select">
            <option :value="null">None</option>
            <option v-for="entry in entries" :key="entry.id" :value="entry.id">
              #{{ entry.id }} - {{ entry.activity.substring(0, 50) }}...
            </option>
          </select>
        </div>

        <div style="display: flex; gap: 12px; justify-content: flex-end">
          <button type="button" class="btn-secondary" @click="form = { activity: '', type: 'LOG', follow_up: '', status: '', reference_id: null, eta: '' }">
            Reset
          </button>
          <button type="submit" class="btn-primary" :disabled="loading">
            {{ loading ? 'Creating...' : 'Create Entry' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
