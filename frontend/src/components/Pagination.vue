<template>
  <div class="flex items-center justify-between">
    <div class="text-sm text-gray-700">
      显示 <span class="font-medium">{{ startItem }}</span> 到
      <span class="font-medium">{{ endItem }}</span>，共
      <span class="font-medium">{{ total }}</span> 条
    </div>

    <nav class="flex items-center space-x-2">
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="px-3 py-2 rounded-md text-sm font-medium border transition-colors"
        :class="
          currentPage === 1
            ? 'border-gray-200 text-gray-400 cursor-not-allowed'
            : 'border-gray-300 text-gray-700 hover:bg-gray-50'
        "
      >
        上一页
      </button>

      <template v-for="page in visiblePages" :key="page">
        <button
          v-if="page !== '...'"
          @click="goToPage(page as number)"
          class="px-3 py-2 rounded-md text-sm font-medium border transition-colors"
          :class="
            page === currentPage
              ? 'border-primary-600 bg-primary-50 text-primary-600'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
          "
        >
          {{ page }}
        </button>
        <span v-else class="px-2 text-gray-500">...</span>
      </template>

      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="px-3 py-2 rounded-md text-sm font-medium border transition-colors"
        :class="
          currentPage === totalPages
            ? 'border-gray-200 text-gray-400 cursor-not-allowed'
            : 'border-gray-300 text-gray-700 hover:bg-gray-50'
        "
      >
        下一页
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  total: number
  limit: number
  offset: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:offset': [value: number]
}>()

const currentPage = computed(() => Math.floor(props.offset / props.limit) + 1)
const totalPages = computed(() => Math.ceil(props.total / props.limit))
const startItem = computed(() => props.offset + 1)
const endItem = computed(() => Math.min(props.offset + props.limit, props.total))

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const delta = 2 // Show 2 pages before and after current page

  for (let i = 1; i <= totalPages.value; i++) {
    if (
      i === 1 ||
      i === totalPages.value ||
      (i >= currentPage.value - delta && i <= currentPage.value + delta)
    ) {
      pages.push(i)
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...')
    }
  }

  return pages
})

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  const newOffset = (page - 1) * props.limit
  emit('update:offset', newOffset)
}
</script>
