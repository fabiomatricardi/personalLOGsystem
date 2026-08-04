import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'fs'
import { resolve } from 'path'

let backendPort = 8000
try {
  const configPath = resolve(__dirname, '..', 'config.json')
  const config = JSON.parse(readFileSync(configPath, 'utf-8'))
  backendPort = config.app?.port || 8000
} catch (e) {
  // Use default if config.json not found
}

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': `http://localhost:${backendPort}`,
    },
  },
})
