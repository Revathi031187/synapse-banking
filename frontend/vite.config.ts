import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Use base path only in production, root path for dev
  base: process.env.NODE_ENV === 'production' ? '/nba-platform/v3/' : '/',
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

