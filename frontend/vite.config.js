import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El backend Flask corre en http://localhost:5000 (ver backend/api.py).
// En desarrollo, /api se redirige automáticamente hacia allá.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
