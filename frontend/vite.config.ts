import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
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
    allowedHosts: ['localhost', 'litea.1uvu.com', 'litea.wlb.life'],
    proxy: {
      "/api": {
        target: "http://localhost:6060",
        changeOrigin: true,
      },
    },
  },
})
