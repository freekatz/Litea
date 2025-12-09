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
    port: 80,
    host: true,
    allowedHosts: ['localhost', 'litea.1uvu.com'],
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
    port: 80,
    host: true,
    allowedHosts: ['localhost', 'litea.1uvu.com'],
    proxy: {
      "/api": {
        target: "http://localhost:6060",
        changeOrigin: true,
      },
    },
  },
  
  // 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false, // 生产环境不生成sourcemap
    minify: 'terser', // 使用terser压缩
    terserOptions: {
      compress: {
        drop_console: true, // 移除console
        drop_debugger: true, // 移除debugger
      },
    },
    rollupOptions: {
      output: {
        // 静态资源分类打包
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
        manualChunks: {
          // 将第三方库分离打包
          'vue-vendor': ['vue', 'vue-router'],
        },
      },
    },
    chunkSizeWarningLimit: 1000, // chunk大小警告限制(kb)
  },
})
