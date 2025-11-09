<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Back Button -->
    <router-link to="/documents" class="inline-flex items-center text-gray-600 hover:text-gray-900">
      <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      返回文献列表
    </router-link>

    <!-- Loading State -->
    <LoadingSpinner v-if="loading" message="加载文献详情..." />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Document Detail -->
    <div v-else-if="document" class="space-y-6">
      <!-- Header Card -->
      <div class="card">
        <div class="flex items-start justify-between mb-4">
          <span
            class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800"
          >
            {{ sourceNames[document.source] || document.source }}
          </span>
          <div class="flex items-center gap-2">
            <button
              v-if="!document.zotero_key"
              @click="exportToZotero"
              class="btn btn-secondary btn-sm"
            >
              <svg class="w-4 h-4 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              导出到 Zotero
            </button>
            <span v-else class="text-sm text-green-600 flex items-center">
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              已导出
            </span>
          </div>
        </div>

        <h1 class="text-3xl font-serif font-bold text-gray-900 mb-4">
          {{ document.title }}
        </h1>

        <!-- Metadata -->
        <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-4">
          <div v-if="document.authors.length > 0" class="flex items-center">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span>
              {{ document.authors.slice(0, 5).join(', ') }}
              <span v-if="document.authors.length > 5"> 等 {{ document.authors.length }} 人</span>
            </span>
          </div>
          <div v-if="document.published_date" class="flex items-center">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>{{ formatDate(document.published_date) }}</span>
          </div>
          <div v-if="document.citation_count !== undefined" class="flex items-center">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
            <span>{{ document.citation_count }} 次引用</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-wrap gap-3">
          <a
            v-if="document.url"
            :href="document.url"
            target="_blank"
            class="btn btn-primary"
          >
            <svg class="w-4 h-4 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            查看原文
          </a>
          <a
            v-if="document.pdf_url"
            :href="document.pdf_url"
            target="_blank"
            class="btn btn-secondary"
          >
            <svg class="w-4 h-4 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            下载 PDF
          </a>
          <button
            @click="copyToClipboard"
            class="btn btn-secondary"
          >
            <svg class="w-4 h-4 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-2M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
            复制引用
          </button>
        </div>
      </div>

      <!-- Keywords -->
      <div v-if="document.keywords && document.keywords.length > 0" class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">关键词</h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="keyword in document.keywords"
            :key="keyword"
            class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800"
          >
            {{ keyword }}
          </span>
        </div>
      </div>

      <!-- Abstract -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">摘要</h2>
        <p class="text-gray-700 leading-relaxed whitespace-pre-line">
          {{ document.abstract || '暂无摘要' }}
        </p>
      </div>

      <!-- AI Summary -->
      <div v-if="document.summary" class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">AI 智能摘要</h2>
        
        <div class="space-y-4">
          <div v-if="document.summary.summary">
            <h3 class="text-sm font-medium text-gray-700 mb-2">核心内容</h3>
            <p class="text-gray-700 leading-relaxed">
              {{ document.summary.summary }}
            </p>
          </div>

          <div v-if="document.summary.highlights && document.summary.highlights.length > 0">
            <h3 class="text-sm font-medium text-gray-700 mb-2">重点亮点</h3>
            <ul class="space-y-2">
              <li
                v-for="(highlight, index) in document.summary.highlights"
                :key="index"
                class="flex items-start"
              >
                <svg class="w-5 h-5 text-primary-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <span class="text-gray-700">{{ highlight }}</span>
              </li>
            </ul>
          </div>

          <div v-if="document.summary.research_trends && document.summary.research_trends.length > 0">
            <h3 class="text-sm font-medium text-gray-700 mb-2">研究趋势</h3>
            <ul class="space-y-2">
              <li
                v-for="(trend, index) in document.summary.research_trends"
                :key="index"
                class="flex items-start"
              >
                <svg class="w-5 h-5 text-green-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd" />
                </svg>
                <span class="text-gray-700">{{ trend }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Metadata -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">元数据</h2>
        <dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt class="text-sm font-medium text-gray-500">文献 ID</dt>
            <dd class="mt-1 text-sm text-gray-900 font-mono">{{ document.external_id }}</dd>
          </div>
          <div v-if="document.created_at">
            <dt class="text-sm font-medium text-gray-500">收录时间</dt>
            <dd class="mt-1 text-sm text-gray-900">{{ formatDate(document.created_at) }}</dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-gray-500">所属任务</dt>
            <dd class="mt-1 text-sm text-gray-900">
              <router-link :to="`/tasks/${document.task_id}`" class="text-primary-600 hover:text-primary-700">
                任务 #{{ document.task_id }}
              </router-link>
            </dd>
          </div>
          <div v-if="document.rank_score !== undefined">
            <dt class="text-sm font-medium text-gray-500">相关性评分</dt>
            <dd class="mt-1 text-sm text-gray-900">{{ (document.rank_score * 100).toFixed(1) }}%</dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- Export Dialog -->
    <div v-if="showExportDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold mb-4">导出到 Zotero</h3>
        <div class="mb-4">
          <label class="label">集合名称</label>
          <input
            v-model="exportCollectionName"
            type="text"
            placeholder="输入 Zotero 集合名称"
            class="input w-full"
            @keyup.enter="confirmExport"
          />
          <p class="text-sm text-gray-500 mt-2">
            如果集合不存在，将自动创建
          </p>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="showExportDialog = false" class="btn btn-secondary">
            取消
          </button>
          <button @click="confirmExport" class="btn btn-primary">
            确认导出
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDocumentStore } from '@/stores/document'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import { formatDate } from '@/utils/helpers'
import { copyToClipboard as copyText } from '@/utils/clipboard'

const route = useRoute()
const documentStore = useDocumentStore()

const documentId = computed(() => Number(route.params.id))
const loading = ref(false)
const error = ref('')
const document = computed(() => documentStore.documents.find(d => d.id === documentId.value))
const showExportDialog = ref(false)
const exportCollectionName = ref('')

const sourceNames: Record<string, string> = {
  arxiv: 'arXiv',
  pubmed: 'PubMed',
  semantic_scholar: 'Semantic Scholar'
}

onMounted(async () => {
  await loadDocumentDetail()
})

async function loadDocumentDetail() {
  loading.value = true
  error.value = ''
  
  try {
    // Ensure document is loaded
    if (!document.value) {
      await documentStore.fetchDocuments({ page: 1, page_size: 100 })
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载文献详情失败'
  } finally {
    loading.value = false
  }
}

async function exportToZotero() {
  if (!document.value) return
  showExportDialog.value = true
}

async function confirmExport() {
  if (!document.value) return
  if (!exportCollectionName.value.trim()) {
    alert('请输入 Zotero 集合名称')
    return
  }
  
  try {
    await documentStore.exportToZotero([document.value.id], exportCollectionName.value)
    alert(`成功导出到 "${exportCollectionName.value}"`)
    showExportDialog.value = false
    exportCollectionName.value = ''
  } catch (e: any) {
    alert(e.response?.data?.detail || e.response?.data?.error || '导出到 Zotero 失败')
  }
}

function copyToClipboard() {
  if (!document.value) return
  
  const citation = `${document.value.authors.slice(0, 3).join(', ')}${document.value.authors.length > 3 ? ' et al.' : ''}. ${document.value.title}. ${document.value.published_date ? new Date(document.value.published_date).getFullYear() : ''}.`
  
  copyText(citation)
  alert('引用格式已复制到剪贴板')
}
</script>
