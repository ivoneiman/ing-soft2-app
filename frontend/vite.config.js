import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // Proxy: las llamadas a /api se redirigen al backend de Flask
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        credentials: true,
      }
    }
  }
})
