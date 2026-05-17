import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.API_TARGET || 'http://localhost:8000'
const inDocker = !!process.env.DOCKER

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    open: !inDocker,
    watch: {
      // bind-mount file events on macOS Docker are unreliable; poll instead
      usePolling: inDocker
    },
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true
      }
    }
  }
})
