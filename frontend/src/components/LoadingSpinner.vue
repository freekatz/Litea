<template>
  <div class="flex items-center justify-center" :class="containerClass">
    <div class="relative" :style="{ width: size, height: size }">
      <div
        class="absolute inset-0 border-4 border-gray-200 rounded-full"
      ></div>
      <div
        class="absolute inset-0 border-4 border-primary-600 rounded-full border-t-transparent animate-spin"
      ></div>
    </div>
    <span v-if="message" class="ml-3 text-gray-600">{{ message }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  message?: string
  fullScreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  fullScreen: false
})

const sizeMap = {
  sm: '24px',
  md: '40px',
  lg: '64px'
}

const size = computed(() => sizeMap[props.size])

const containerClass = computed(() => {
  return props.fullScreen
    ? 'fixed inset-0 bg-white bg-opacity-75 z-50'
    : 'py-8'
})
</script>
