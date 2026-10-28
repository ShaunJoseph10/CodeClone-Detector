/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  return {
    plugins: [react(), tailwindcss()],
    server: {
      // dev: /api is proxied to the FastAPI backend
      proxy: { '/api': env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000', '/docs': env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000' },
    },
    test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], css: false },
  }
})
