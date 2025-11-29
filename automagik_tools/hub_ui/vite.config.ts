import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Read backend port from environment (set by dev_runner.sh)
// Falls back to 8000 for standalone frontend dev
const backendPort = process.env.VITE_BACKEND_PORT || '8000';
const backendUrl = `http://localhost:${backendPort}`;

// https://vite.dev/config/
export default defineConfig({
  base: '/',  // Deploy at root path
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Make backend port available to client code
  define: {
    'import.meta.env.VITE_BACKEND_PORT': JSON.stringify(backendPort),
  },
  server: {
    host: '0.0.0.0',
    // Port can be overridden via CLI: pnpm dev --port 3000
    port: 3000,
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/mcp': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/health': {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
})
