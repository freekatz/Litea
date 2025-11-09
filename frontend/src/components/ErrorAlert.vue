<template>
  <div
    v-if="visible"
    class="rounded-lg p-4 mb-4 flex items-start"
    :class="typeClasses"
    role="alert"
  >
    <div class="flex-shrink-0">
      <svg
        v-if="type === 'error'"
        class="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fill-rule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
          clip-rule="evenodd"
        />
      </svg>
      <svg
        v-else-if="type === 'warning'"
        class="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fill-rule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clip-rule="evenodd"
        />
      </svg>
      <svg
        v-else
        class="w-5 h-5"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fill-rule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
          clip-rule="evenodd"
        />
      </svg>
    </div>
    <div class="ml-3 flex-1">
      <p class="text-sm font-medium">{{ message }}</p>
      <p v-if="details" class="text-sm mt-1 opacity-90">{{ details }}</p>
    </div>
    <button
      v-if="dismissible"
      @click="visible = false"
      class="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 inline-flex hover:bg-black hover:bg-opacity-10"
    >
      <span class="sr-only">关闭</span>
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path
          fill-rule="evenodd"
          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
          clip-rule="evenodd"
        />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  type?: 'error' | 'warning' | 'success' | 'info'
  message: string
  details?: string
  dismissible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'error',
  dismissible: true
})

const visible = ref(true)

const typeClasses = computed(() => {
  const classes = {
    error: 'bg-red-50 text-red-800 border border-red-200',
    warning: 'bg-yellow-50 text-yellow-800 border border-yellow-200',
    success: 'bg-green-50 text-green-800 border border-green-200',
    info: 'bg-blue-50 text-blue-800 border border-blue-200'
  }
  return classes[props.type]
})
</script>
