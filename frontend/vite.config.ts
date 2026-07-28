import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

declare const process: { env: Record<string, string | undefined> }

export default defineConfig({
  plugins: [react()],
  // Base path: VITE_BASE_PATH for deployment (e.g. /banking-platform/v1), else /nba-platform/v3 in prod
  base: process.env.VITE_BASE_PATH ? `${process.env.VITE_BASE_PATH.replace(/\/$/, '')}/` : (process.env.NODE_ENV === 'production' ? '/nba-platform/v3/' : '/'),
  server: {
    port: 5173,  // Standard Vite port
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      }
    }
  }
})

