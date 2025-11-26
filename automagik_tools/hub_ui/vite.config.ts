import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: '/',  // Deploy at root path
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 9884,
    proxy: {
      '/api': {
        target: 'http://localhost:8884',
        changeOrigin: true,
      },
      '/mcp': {
        target: 'http://localhost:8884',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8884',
        changeOrigin: true,
      },
    },
  },
})
