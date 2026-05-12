import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: '0.0.0.0', // necessário para o Vite responder dentro do Docker
    port: 5173,
    proxy: {
      // Toda requisição para /api será redirecionada para o backend
      // dentro da rede Docker, usando o nome do serviço "backend"
      '/api': {
        target: process.env.VITE_BACKEND_INTERNAL_URL || 'http://backend:5000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
