<template>
  <div id="app" class="h-screen flex flex-col bg-gray-50">
    <!-- 顶部导航 -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-4">
        <div class="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center shadow-md">
          <span class="text-white text-2xl">☕</span>
        </div>
        <div class="flex flex-col">
          <h1 class="text-2xl font-serif font-bold text-gray-900 leading-tight">
            Litea: Literature with a cup of tea!
          </h1>
          <p class="text-xs text-gray-500 mt-0.5">
            — Effortless self-hosted all-in-one academic literature assistant.
          </p>
        </div>
      </div>
      <a 
        href="https://github.com/freekatz/Litea" 
        target="_blank"
        rel="noopener noreferrer"
        class="github-link"
        title="View on GitHub"
      >
        <svg height="32" width="32" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
        </svg>
      </a>
    </header>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
// Minimal app layout
</script>

<style>
.github-link {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #24292e;
  transition: all 0.2s;
}

.github-link:hover {
  color: #0366d6;
  transform: scale(1.1);
}

.github-link svg {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Header Gradient Background */
header {
  background: linear-gradient(to bottom, #ffffff 0%, #fefefe 100%);
}

/* Icon gradient */
.bg-gradient-to-br {
  background-image: linear-gradient(to bottom right, var(--tw-gradient-stops));
}

.from-amber-500 {
  --tw-gradient-from: #f59e0b;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(245, 158, 11, 0));
}

.to-orange-600 {
  --tw-gradient-to: #ea580c;
}

.shadow-md {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.rounded-lg {
  border-radius: 0.5rem;
}

.leading-tight {
  line-height: 1.25;
}

.bg-primary-600 {
  background-color: #2563eb;
}

.text-primary-600 {
  color: #2563eb;
}

.border-primary-300 {
  border-color: #93c5fd;
}

.bg-primary-50 {
  background-color: #eff6ff;
}

.text-primary-700 {
  color: #1d4ed8;
}

.hover\:bg-primary-700:hover {
  background-color: #1d4ed8;
}

.focus\:ring-primary-500:focus {
  --tw-ring-color: #3b82f6;
}
</style>
