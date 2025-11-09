<template>
  <div class="flex gap-4 h-[calc(100vh-12rem)]">
    <!-- 左侧：任务列表 (30%) -->
    <div class="w-1/3 flex flex-col bg-white rounded-lg shadow overflow-hidden">
      <div class="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
        <h2 class="font-semibold text-gray-900">检索任务</h2>
        <button @click="showTaskForm = true" class="text-sm bg-primary-600 text-white px-3 py-1 rounded hover:bg-primary-700">
          + 新建
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto p-3 space-y-2">
        <div v-if="loadingTasks" class="text-center py-8 text-gray-500">加载中...</div>
        <div v-else-if="tasks.length === 0" class="text-center py-8 text-gray-400">
          <p>还没有任务</p>
          <p class="text-xs mt-1">点击右上角创建第一个检索任务</p>
        </div>
        <div
          v-for="task in tasks"
          :key="task.id"
          @click="selectedTask = task"
          :class="[
            'p-3 rounded-lg cursor-pointer transition-colors border',
            selectedTask?.id === task.id 
              ? 'bg-primary-50 border-primary-300' 
              : 'bg-white border-gray-200 hover:border-gray-300'
          ]"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <h3 class="font-medium text-sm text-gray-900 truncate">{{ task.name }}</h3>
              <p class="text-xs text-gray-500 mt-1 line-clamp-2">{{ task.prompt }}</p>
            </div>
            <span :class="[
              'text-xs px-2 py-0.5 rounded-full ml-2 flex-shrink-0',
              task.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
            ]">
              {{ task.status === 'active' ? '运行中' : '已停止' }}
            </span>
          </div>
          <div class="mt-2 flex items-center gap-3 text-xs text-gray-500">
            <span>{{ task.keywords.length }} 关键词</span>
            <span>{{ task.sources.length }} 数据源</span>
            <span v-if="task.last_run_at">
              {{ formatDate(task.last_run_at) }}
            </span>
          </div>
          <div class="mt-2 flex gap-1">
            <button
              v-if="task.status !== 'active'"
              @click.stop="startTask(task.id)"
              class="text-xs text-green-600 hover:text-green-700"
            >启动</button>
            <button
              v-else
              @click.stop="stopTask(task.id)"
              class="text-xs text-red-600 hover:text-red-700"
            >停止</button>
            <span class="text-gray-300">|</span>
            <button @click.stop="editTask(task)" class="text-xs text-blue-600 hover:text-blue-700">编辑</button>
            <span class="text-gray-300">|</span>
            <button @click.stop="deleteTask(task.id)" class="text-xs text-red-600 hover:text-red-700">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：文献列表和详情 (70%) -->
    <div class="flex-1 flex flex-col bg-white rounded-lg shadow overflow-hidden">
      <div class="px-4 py-3 bg-gray-50 border-b">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-semibold text-gray-900">
            {{ selectedTask ? selectedTask.name + ' - 文献列表' : '全部文献' }}
          </h2>
          <div class="flex gap-2">
            <button
              v-if="selectedTask"
              @click="showAnalytics = !showAnalytics"
              class="text-sm text-gray-600 hover:text-gray-900"
            >
              {{ showAnalytics ? '📊 隐藏统计' : '📈 查看统计' }}
            </button>
            <button
              @click="loadDocuments"
              class="text-sm text-gray-600 hover:text-gray-900"
            >🔄 刷新</button>
          </div>
        </div>
        
        <!-- 搜索和过滤 -->
        <div class="flex gap-2">
          <input
            v-model="searchQuery"
            @input="debouncedSearch"
            type="text"
            placeholder="搜索标题、作者、关键词..."
            class="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          <select
            v-model="filterSource"
            @change="loadDocuments"
            class="px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            <option value="">所有来源</option>
            <option value="arxiv">arXiv</option>
            <option value="pubmed">PubMed</option>
          </select>
        </div>
      </div>

      <!-- 统计面板 (可折叠) -->
      <div v-if="showAnalytics && selectedTask" class="px-4 py-3 bg-blue-50 border-b grid grid-cols-4 gap-3">
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ stats.total || 0 }}</div>
          <div class="text-xs text-gray-600">总文献数</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ stats.thisWeek || 0 }}</div>
          <div class="text-xs text-gray-600">本周新增</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-purple-600">{{ stats.avgScore || 0 }}</div>
          <div class="text-xs text-gray-600">平均得分</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-orange-600">{{ stats.sources || 0 }}</div>
          <div class="text-xs text-gray-600">数据源数</div>
        </div>
      </div>

      <!-- 文献列表 -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="loadingDocs" class="text-center py-12 text-gray-500">加载文献...</div>
        <div v-else-if="documents.length === 0" class="text-center py-12 text-gray-400">
          <p>{{ selectedTask ? '该任务还没有检索到文献' : '还没有文献' }}</p>
          <p class="text-xs mt-1">启动任务后将自动检索文献</p>
        </div>
        <div v-else class="divide-y divide-gray-200">
          <div
            v-for="doc in documents"
            :key="doc.id"
            @click="selectedDoc = doc"
            :class="[
              'p-4 cursor-pointer transition-colors',
              selectedDoc?.id === doc.id ? 'bg-blue-50' : 'hover:bg-gray-50'
            ]"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0 pr-4">
                <h3 class="font-medium text-gray-900 line-clamp-2 text-sm">
                  {{ doc.title }}
                </h3>
                <div class="mt-1 flex items-center gap-3 text-xs text-gray-500">
                  <span v-if="doc.authors.length">{{ doc.authors.slice(0, 2).join(', ') }}</span>
                  <span v-if="doc.published_at">{{ formatDate(doc.published_at) }}</span>
                  <span class="px-1.5 py-0.5 bg-gray-100 rounded">{{ doc.source_name }}</span>
                  <span v-if="doc.rank_score" class="text-green-600">⭐ {{ (doc.rank_score * 100).toFixed(0) }}</span>
                </div>
                <p v-if="doc.abstract" class="mt-2 text-xs text-gray-600 line-clamp-2">
                  {{ doc.abstract }}
                </p>
                <div v-if="doc.keywords.length" class="mt-2 flex flex-wrap gap-1">
                  <span
                    v-for="kw in doc.keywords.slice(0, 5)"
                    :key="kw"
                    class="text-xs px-1.5 py-0.5 bg-primary-50 text-primary-700 rounded"
                  >{{ kw }}</span>
                </div>
              </div>
              <div class="flex flex-col gap-1">
                <a
                  v-if="doc.url"
                  :href="doc.url"
                  target="_blank"
                  @click.stop
                  class="text-xs text-blue-600 hover:text-blue-700"
                >查看原文 ↗</a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="px-4 py-3 bg-gray-50 border-t flex items-center justify-between text-sm">
        <div class="text-gray-600">
          共 {{ totalDocs }} 篇，第 {{ currentPage }}/{{ totalPages }} 页
        </div>
        <div class="flex gap-1">
          <button
            @click="currentPage--; loadDocuments()"
            :disabled="currentPage === 1"
            class="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >上一页</button>
          <button
            @click="currentPage++; loadDocuments()"
            :disabled="currentPage === totalPages"
            class="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >下一页</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 任务表单弹窗 -->
  <TaskFormModal
    v-if="showTaskForm"
    :task="editingTask"
    @close="showTaskForm = false; editingTask = null"
    @saved="onTaskSaved"
  />

  <!-- 文献详情弹窗 -->
  <DocumentDetailModal
    v-if="selectedDoc"
    :document="selectedDoc"
    @close="selectedDoc = null"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { tasksApi } from '@/api/tasks'
import { documentsApi } from '@/api/documents'
import TaskFormModal from '@/components/tasks/TaskFormModal.vue'
import DocumentDetailModal from '@/components/documents/DocumentDetailModal.vue'
import type { Task, Document } from '@/types'

const tasks = ref<Task[]>([])
const documents = ref<Document[]>([])
const selectedTask = ref<Task | null>(null)
const selectedDoc = ref<Document | null>(null)
const loadingTasks = ref(false)
const loadingDocs = ref(false)
const showTaskForm = ref(false)
const editingTask = ref<Task | null>(null)
const showAnalytics = ref(false)

const searchQuery = ref('')
const filterSource = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalDocs = ref(0)
const totalPages = computed(() => Math.ceil(totalDocs.value / pageSize.value))

const stats = ref({
  total: 0,
  thisWeek: 0,
  avgScore: 0,
  sources: 0
})

// 加载任务列表
async function loadTasks() {
  loadingTasks.value = true
  try {
    const response = await tasksApi.list()
    tasks.value = response.data.data
    if (tasks.value.length > 0 && !selectedTask.value) {
      selectedTask.value = tasks.value[0]
    }
  } catch (error) {
    console.error('Failed to load tasks:', error)
  } finally {
    loadingTasks.value = false
  }
}

// 加载文献列表
async function loadDocuments() {
  loadingDocs.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (selectedTask.value) {
      params.task_id = selectedTask.value.id
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    if (filterSource.value) {
      params.source = filterSource.value
    }

    const response = await documentsApi.list(params)
    documents.value = response.data.data
    totalDocs.value = response.data.total || documents.value.length
  } catch (error) {
    console.error('Failed to load documents:', error)
  } finally {
    loadingDocs.value = false
  }
}

// 防抖搜索
let searchTimeout: number
function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = window.setTimeout(() => {
    currentPage.value = 1
    loadDocuments()
  }, 500)
}

// 任务操作
async function startTask(id: number) {
  try {
    await tasksApi.start(id)
    await loadTasks()
  } catch (error) {
    console.error('Failed to start task:', error)
  }
}

async function stopTask(id: number) {
  try {
    await tasksApi.stop(id)
    await loadTasks()
  } catch (error) {
    console.error('Failed to stop task:', error)
  }
}

function editTask(task: Task) {
  editingTask.value = task
  showTaskForm.value = true
}

async function deleteTask(id: number) {
  if (!confirm('确定要删除这个任务吗？任务及其关联的所有文献都将被永久删除，此操作不可恢复。')) return
  try {
    await tasksApi.delete(id)
    await loadTasks()
    if (selectedTask.value?.id === id) {
      selectedTask.value = tasks.value[0] || null
    }
  } catch (error) {
    console.error('Failed to delete task:', error)
  }
}

function onTaskSaved() {
  showTaskForm.value = false
  editingTask.value = null
  loadTasks()
}

// 格式化日期
function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })
}

// 监听任务切换
watch(selectedTask, () => {
  currentPage.value = 1
  loadDocuments()
})

onMounted(() => {
  loadTasks()
  loadDocuments()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
