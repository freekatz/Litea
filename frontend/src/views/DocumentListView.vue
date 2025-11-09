<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-serif font-bold text-gray-900">文献库</h1>
        <p class="mt-2 text-sm text-gray-600">
          浏览和管理检索到的文献资料
        </p>
      </div>
      <button
        v-if="selectedDocuments.length > 0"
        @click="exportToZotero"
        class="btn btn-primary"
      >
        <svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        导出到 Zotero ({{ selectedDocuments.length }})
      </button>
    </div>

    <!-- Filters -->
    <div class="card">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <input
          v-model="filters.search"
          type="text"
          placeholder="搜索标题、作者、关键词..."
          class="input md:col-span-2"
        />
        <select v-model="filters.source" class="input">
          <option value="">所有来源</option>
          <option value="arxiv">arXiv</option>
          <option value="pubmed">PubMed</option>
          <option value="semantic_scholar">Semantic Scholar</option>
        </select>
        <select v-model="filters.sort" class="input">
          <option value="published_desc">发布时间 ↓</option>
          <option value="published_asc">发布时间 ↑</option>
          <option value="citations_desc">引用量 ↓</option>
          <option value="title_asc">标题 A-Z</option>
        </select>
      </div>

      <!-- Advanced Filters Toggle -->
      <div class="mt-4">
        <button
          @click="showAdvancedFilters = !showAdvancedFilters"
          class="text-sm text-primary-600 hover:text-primary-700"
        >
          {{ showAdvancedFilters ? '隐藏高级筛选 ▲' : '显示高级筛选 ▼' }}
        </button>
      </div>

      <!-- Advanced Filters -->
      <div v-if="showAdvancedFilters" class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
        <div>
          <label class="label">发布年份</label>
          <div class="flex gap-2">
            <input
              v-model.number="filters.yearFrom"
              type="number"
              placeholder="从"
              class="input"
            />
            <input
              v-model.number="filters.yearTo"
              type="number"
              placeholder="到"
              class="input"
            />
          </div>
        </div>
        <div>
          <label class="label">引用量范围</label>
          <div class="flex gap-2">
            <input
              v-model.number="filters.citationsMin"
              type="number"
              placeholder="最小"
              class="input"
            />
            <input
              v-model.number="filters.citationsMax"
              type="number"
              placeholder="最大"
              class="input"
            />
          </div>
        </div>
        <div>
          <label class="label">所属任务</label>
          <select v-model="filters.taskId" class="input">
            <option value="">所有任务</option>
            <option v-for="task in tasks" :key="task.id" :value="task.id">
              {{ task.name }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Bulk Actions -->
    <div v-if="selectedDocuments.length > 0" class="card bg-primary-50 border-primary-200">
      <div class="flex items-center justify-between">
        <span class="text-sm text-primary-900">
          已选择 {{ selectedDocuments.length }} 篇文献
        </span>
        <div class="flex gap-2">
          <button @click="clearSelection" class="btn btn-secondary btn-sm">
            取消选择
          </button>
          <button @click="exportToZotero" class="btn btn-primary btn-sm">
            导出到 Zotero
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <LoadingSpinner v-if="loading" message="加载文献列表..." />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Empty State -->
    <div v-else-if="documents.length === 0" class="card text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">暂无文献</h3>
      <p class="mt-1 text-sm text-gray-500">执行检索任务后，文献将显示在此处</p>
      <div class="mt-6">
        <router-link to="/tasks" class="btn btn-primary">
          前往任务管理
        </router-link>
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

    <!-- Document List -->
    <div v-else class="space-y-4">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="card hover:shadow-md transition-shadow"
      >
        <div class="flex items-start gap-4">
          <!-- Checkbox -->
          <input
            type="checkbox"
            :checked="selectedDocuments.includes(doc.id)"
            @change="toggleSelection(doc.id)"
            class="mt-1 w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
          />

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1">
                <router-link
                  :to="`/documents/${doc.id}`"
                  class="text-lg font-serif font-semibold text-gray-900 hover:text-primary-600 line-clamp-2"
                >
                  {{ doc.title }}
                </router-link>
                <div class="mt-1 flex items-center gap-4 text-sm text-gray-600">
                  <span v-if="doc.authors.length > 0">
                    {{ doc.authors.slice(0, 3).join(', ') }}
                    <span v-if="doc.authors.length > 3"> 等</span>
                  </span>
                  <span v-if="doc.published_date">
                    {{ formatDate(doc.published_date) }}
                  </span>
                  <span v-if="doc.citation_count !== undefined" class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                    {{ doc.citation_count }}
                  </span>
                </div>
              </div>

              <!-- Source Badge -->
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {{ sourceNames[doc.source] || doc.source }}
              </span>
            </div>

            <!-- Abstract -->
            <p v-if="doc.abstract" class="mt-3 text-sm text-gray-600 line-clamp-3">
              {{ doc.abstract }}
            </p>

            <!-- Keywords -->
            <div v-if="doc.keywords && doc.keywords.length > 0" class="mt-3 flex flex-wrap gap-1">
              <span
                v-for="keyword in doc.keywords.slice(0, 8)"
                :key="keyword"
                class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-50 text-primary-700"
              >
                {{ keyword }}
              </span>
            </div>

            <!-- Actions -->
            <div class="mt-4 flex items-center gap-4 text-sm">
              <a
                v-if="doc.pdf_url"
                :href="doc.pdf_url"
                target="_blank"
                class="text-primary-600 hover:text-primary-700 flex items-center"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                下载 PDF
              </a>
              <a
                v-if="doc.url"
                :href="doc.url"
                target="_blank"
                class="text-primary-600 hover:text-primary-700 flex items-center"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                查看原文
              </a>
              <router-link
                :to="`/documents/${doc.id}`"
                class="text-primary-600 hover:text-primary-700 flex items-center"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                详细信息
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <Pagination
      v-if="totalPages > 1"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      @update:current-page="handlePageChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentStore } from '@/stores/document'
import { useTaskStore } from '@/stores/task'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import Pagination from '@/components/Pagination.vue'
import { formatDate } from '@/utils/helpers'

const router = useRouter()
const documentStore = useDocumentStore()
const taskStore = useTaskStore()

const showAdvancedFilters = ref(false)
const selectedDocuments = ref<number[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const showExportDialog = ref(false)
const exportCollectionName = ref('')

const filters = ref({
  search: '',
  source: '',
  sort: 'published_desc',
  yearFrom: undefined as number | undefined,
  yearTo: undefined as number | undefined,
  citationsMin: undefined as number | undefined,
  citationsMax: undefined as number | undefined,
  taskId: ''
})

const loading = computed(() => documentStore.loading)
const error = computed(() => documentStore.error)
const documents = computed(() => documentStore.documents)
const totalItems = computed(() => documentStore.total)
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))
const tasks = computed(() => taskStore.tasks)

const sourceNames: Record<string, string> = {
  arxiv: 'arXiv',
  pubmed: 'PubMed',
  semantic_scholar: 'Semantic Scholar'
}

onMounted(async () => {
  await Promise.all([
    loadDocuments(),
    taskStore.fetchTasks()
  ])
})

watch(filters, () => {
  currentPage.value = 1
  loadDocuments()
}, { deep: true })

async function loadDocuments() {
  await documentStore.fetchDocuments({
    page: currentPage.value,
    page_size: pageSize.value,
    search: filters.value.search || undefined,
    source: filters.value.source || undefined,
    sort: filters.value.sort,
    year_from: filters.value.yearFrom,
    year_to: filters.value.yearTo,
    citations_min: filters.value.citationsMin,
    citations_max: filters.value.citationsMax,
    task_id: filters.value.taskId ? Number(filters.value.taskId) : undefined
  })
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadDocuments()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function toggleSelection(docId: number) {
  const index = selectedDocuments.value.indexOf(docId)
  if (index > -1) {
    selectedDocuments.value.splice(index, 1)
  } else {
    selectedDocuments.value.push(docId)
  }
}

function clearSelection() {
  selectedDocuments.value = []
}

async function exportToZotero() {
  if (selectedDocuments.value.length === 0) return
  showExportDialog.value = true
}

async function confirmExport() {
  if (!exportCollectionName.value.trim()) {
    alert('请输入 Zotero 集合名称')
    return
  }

  try {
    await documentStore.exportToZotero(selectedDocuments.value, exportCollectionName.value)
    alert(`成功导出 ${selectedDocuments.value.length} 篇文献到 "${exportCollectionName.value}"`)
    showExportDialog.value = false
    exportCollectionName.value = ''
    clearSelection()
  } catch (e: any) {
    alert(e.response?.data?.detail || e.response?.data?.error || '导出到 Zotero 失败')
  }
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
