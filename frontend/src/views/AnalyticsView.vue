<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-serif font-bold text-gray-900">数据分析</h1>
      <p class="mt-2 text-sm text-gray-600">
        文献检索趋势与统计数据可视化
      </p>
    </div>

    <!-- Time Range Selector -->
    <div class="card">
      <div class="flex items-center gap-4">
        <label class="label">时间范围:</label>
        <select v-model="timeRange" class="input w-48">
          <option value="7d">最近 7 天</option>
          <option value="30d">最近 30 天</option>
          <option value="90d">最近 90 天</option>
          <option value="1y">最近一年</option>
          <option value="all">全部时间</option>
        </select>
        <button @click="loadAnalytics" class="btn btn-secondary">
          <svg class="w-4 h-4 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          刷新
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <LoadingSpinner v-if="loading" message="加载统计数据..." />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Analytics Dashboard -->
    <div v-else class="space-y-6">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">总文献数</p>
              <p class="mt-2 text-3xl font-serif font-bold text-gray-900">
                {{ stats.total_documents.toLocaleString() }}
              </p>
            </div>
            <div class="p-3 bg-primary-100 rounded-lg">
              <svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">活跃任务</p>
              <p class="mt-2 text-3xl font-serif font-bold text-gray-900">
                {{ stats.active_tasks }}
              </p>
            </div>
            <div class="p-3 bg-green-100 rounded-lg">
              <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">本周新增</p>
              <p class="mt-2 text-3xl font-serif font-bold text-gray-900">
                {{ stats.documents_this_week }}
              </p>
              <p class="mt-1 text-xs text-green-600">
                +{{ stats.week_growth_rate }}%
              </p>
            </div>
            <div class="p-3 bg-yellow-100 rounded-lg">
              <svg class="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600">平均引用</p>
              <p class="mt-2 text-3xl font-serif font-bold text-gray-900">
                {{ stats.avg_citations.toFixed(1) }}
              </p>
            </div>
            <div class="p-3 bg-purple-100 rounded-lg">
              <svg class="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row 1 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Trend Chart -->
        <div class="card">
          <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">
            文献收录趋势
          </h2>
          <div class="h-80">
            <canvas ref="trendChartRef"></canvas>
          </div>
        </div>

        <!-- Source Distribution -->
        <div class="card">
          <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">
            数据来源分布
          </h2>
          <div class="h-80">
            <canvas ref="sourceChartRef"></canvas>
          </div>
        </div>
      </div>

      <!-- Charts Row 2 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Top Keywords -->
        <div class="card">
          <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">
            热门关键词 TOP 20
          </h2>
          <div class="h-80">
            <canvas ref="keywordChartRef"></canvas>
          </div>
        </div>

        <!-- Task Performance -->
        <div class="card">
          <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">
            任务执行统计
          </h2>
          <div class="h-80">
            <canvas ref="taskChartRef"></canvas>
          </div>
        </div>
      </div>

      <!-- Top Documents Table -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">
          高引用文献 TOP 10
        </h2>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  标题
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  作者
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  来源
                </th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  引用量
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="doc in topDocuments" :key="doc.id" class="hover:bg-gray-50">
                <td class="px-4 py-3">
                  <router-link :to="`/documents/${doc.id}`" class="text-primary-600 hover:text-primary-700 font-medium">
                    {{ doc.title }}
                  </router-link>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">
                  {{ doc.authors.slice(0, 2).join(', ') }}
                  <span v-if="doc.authors.length > 2"> 等</span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">
                  {{ sourceNames[doc.source] || doc.source }}
                </td>
                <td class="px-4 py-3 text-sm font-medium text-gray-900">
                  {{ doc.citation_count?.toLocaleString() || 0 }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import { Chart, registerables } from 'chart.js'
import type { Document } from '@/types'

Chart.register(...registerables)

const analyticsStore = useAnalyticsStore()

const timeRange = ref('30d')
const loading = ref(false)
const error = ref('')

const trendChartRef = ref<HTMLCanvasElement | null>(null)
const sourceChartRef = ref<HTMLCanvasElement | null>(null)
const keywordChartRef = ref<HTMLCanvasElement | null>(null)
const taskChartRef = ref<HTMLCanvasElement | null>(null)

let trendChart: Chart | null = null
let sourceChart: Chart | null = null
let keywordChart: Chart | null = null
let taskChart: Chart | null = null

const stats = ref({
  total_documents: 0,
  active_tasks: 0,
  documents_this_week: 0,
  week_growth_rate: 0,
  avg_citations: 0
})

const topDocuments = ref<Document[]>([])

const sourceNames: Record<string, string> = {
  arxiv: 'arXiv',
  pubmed: 'PubMed',
  semantic_scholar: 'Semantic Scholar'
}

onMounted(async () => {
  await loadAnalytics()
})

onUnmounted(() => {
  destroyCharts()
})

async function loadAnalytics() {
  loading.value = true
  error.value = ''

  try {
    await analyticsStore.fetchAnalytics({ time_range: timeRange.value })
    
    const data = analyticsStore.analytics
    
    // Update stats
    stats.value = {
      total_documents: data.total_documents || 0,
      active_tasks: data.active_tasks || 0,
      documents_this_week: data.documents_this_week || 0,
      week_growth_rate: data.week_growth_rate || 0,
      avg_citations: data.avg_citations || 0
    }

    topDocuments.value = data.top_documents || []

    // Wait for DOM update
    await nextTick()
    
    // Create charts
    createTrendChart(data.trend_data || [])
    createSourceChart(data.source_distribution || {})
    createKeywordChart(data.top_keywords || [])
    createTaskChart(data.task_stats || [])
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载统计数据失败'
  } finally {
    loading.value = false
  }
}

function destroyCharts() {
  trendChart?.destroy()
  sourceChart?.destroy()
  keywordChart?.destroy()
  taskChart?.destroy()
}

function createTrendChart(data: any[]) {
  if (!trendChartRef.value) return
  
  trendChart?.destroy()
  
  trendChart = new Chart(trendChartRef.value, {
    type: 'line',
    data: {
      labels: data.map(d => d.date),
      datasets: [{
        label: '文献数量',
        data: data.map(d => d.count),
        borderColor: 'rgb(79, 70, 229)',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  })
}

function createSourceChart(data: Record<string, number>) {
  if (!sourceChartRef.value) return
  
  sourceChart?.destroy()
  
  const labels = Object.keys(data).map(k => sourceNames[k] || k)
  const values = Object.values(data)
  
  sourceChart = new Chart(sourceChartRef.value, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: [
          'rgb(79, 70, 229)',
          'rgb(16, 185, 129)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)',
          'rgb(139, 92, 246)'
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  })
}

function createKeywordChart(data: Array<{ keyword: string; count: number }>) {
  if (!keywordChartRef.value) return
  
  keywordChart?.destroy()
  
  keywordChart = new Chart(keywordChartRef.value, {
    type: 'bar',
    data: {
      labels: data.map(d => d.keyword),
      datasets: [{
        label: '出现次数',
        data: data.map(d => d.count),
        backgroundColor: 'rgb(79, 70, 229)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          beginAtZero: true
        }
      }
    }
  })
}

function createTaskChart(data: Array<{ name: string; count: number }>) {
  if (!taskChartRef.value) return
  
  taskChart?.destroy()
  
  taskChart = new Chart(taskChartRef.value, {
    type: 'bar',
    data: {
      labels: data.map(d => d.name),
      datasets: [{
        label: '检索文献数',
        data: data.map(d => d.count),
        backgroundColor: 'rgb(16, 185, 129)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  })
}
</script>
