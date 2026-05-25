import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const apiTarget = process.env.API_TARGET || 'http://localhost:8000'
const inDocker = !!process.env.DOCKER
const webRoot = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // External-device adapters live in `web/src/device/`; expose them as
      // `@device/...` so React components don't need brittle relative paths.
      '@device': path.join(webRoot, 'src', 'device')
    }
  },
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
