<script setup>
defineProps({
  currentView: String
})

const emit = defineEmits(['navigate'])

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: 'pi pi-home' },
  { id: 'timeline', label: 'Log Timeline', icon: 'pi pi-list' },
  { id: 'new-entry', label: 'New Entry', icon: 'pi pi-plus' },
  { id: 'tasks', label: 'Tasks Board', icon: 'pi pi-columns' },
  { id: 'analysis', label: 'Analysis', icon: 'pi pi-chart-bar' },
  { id: 'settings', label: 'Settings', icon: 'pi pi-cog' }
]
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>Personal Log</h1>
    </div>
    <nav class="sidebar-nav">
      <div
        v-for="item in navItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: currentView === item.id }"
        @click="emit('navigate', item.id)"
      >
        <i :class="item.icon"></i>
        <span>{{ item.label }}</span>
      </div>
    </nav>
  </aside>
</template>
