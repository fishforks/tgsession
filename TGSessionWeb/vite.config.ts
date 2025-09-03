import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/get_session': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/check_qr_status': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/active_sessions': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/cleanup_all': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/cleanup': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
}) 