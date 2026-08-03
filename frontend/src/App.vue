<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Dashboard from './components/Dashboard.vue'
import LogTimeline from './components/LogTimeline.vue'
import NewEntry from './components/NewEntry.vue'
import TasksBoard from './components/TasksBoard.vue'
import Analysis from './components/Analysis.vue'
import Settings from './components/Settings.vue'

const currentView = ref('dashboard')
</script>

<template>
  <div class="app-layout">
    <Sidebar :currentView="currentView" @navigate="currentView = $event" />
    <main class="main-content">
      <Dashboard v-if="currentView === 'dashboard'" />
      <LogTimeline v-else-if="currentView === 'timeline'" />
      <NewEntry v-else-if="currentView === 'new-entry'" />
      <TasksBoard v-else-if="currentView === 'tasks'" />
      <Analysis v-else-if="currentView === 'analysis'" />
      <Settings v-else-if="currentView === 'settings'" />
    </main>
  </div>
</template>
