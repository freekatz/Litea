import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const projectRoot = fileURLToPath(new URL('.', import.meta.url))
const sharedDir = fileURLToPath(new URL('../shared', import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@shared': sharedDir
    }
  },
  server: {
    port: 3000,
    host: true,
    allowedHosts: ['localhost'],
    fs: {
      allow: [projectRoot, sharedDir]
    },
    proxy: {
      '/api': {
        target: 'http://localhost:6060',
        changeOrigin: true
      }
    }
  },
  // 生产预览服务器配置
  preview: {
    port: 3000,
    host: true,
    allowedHosts: ['localhost'],
    proxy: {
      "/api": {
        target: "http://localhost:6060",
        changeOrigin: true,
      },
    },
  },
})
