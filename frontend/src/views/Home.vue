<template>
  <div class="home-view" :class="{ resizing: isResizing || isResizingRight }">
    <!-- 左侧任务栏 -->
    <div class="tasks-panel" :style="{ width: leftPanelWidth + 'px' }">
      <div class="panel-header">
        <h2>任务管理</h2>
        <button @click="handleCreateTask" class="btn-create">+ 新建</button>
      </div>
      
      <div class="task-list">
        <!-- 运行中的任务 -->
        <div class="task-group">
          <div class="group-header" @click="showActiveGroup = !showActiveGroup">
            <span class="group-title">
              <span class="group-icon running">▶</span>
              运行中 ({{ activeTasks.length }})
            </span>
            <span class="toggle-icon">{{ showActiveGroup ? '▼' : '▶' }}</span>
          </div>
          
          <div v-if="showActiveGroup" class="group-content">
            <div
              v-for="task in activeTasks"
              :key="task.id"
              class="task-card active"
              :class="{ selected: selectedTaskId === task.id }"
              @click="selectedTaskId = task.id; loadDocuments()"
            >
              <div class="task-info">
                <h3>{{ task.name }}</h3>
                <div class="task-meta">
                  <span class="badge">{{ task.keywords?.length || 0 }} 关键词</span>
                  <span class="badge active-badge">运行中</span>
                </div>
              </div>
              
              <div class="task-actions">
                <button
                  @click.stop="handleStopTask(task)"
                  class="btn-icon"
                  title="停止任务"
                >
                  ■
                </button>
                <button @click.stop="handleCopyTask(task)" class="btn-icon" title="复制配置">📋</button>
                <button @click.stop="handleEditTask(task)" class="btn-icon" title="编辑任务">✎</button>
                <button @click.stop="handleDeleteTask(task)" class="btn-icon danger" title="归档任务">📦</button>
                <button @click.stop="handlePermanentDelete(task)" class="btn-icon danger" title="删除任务">🗑️</button>
              </div>
            </div>
            
            <div v-if="activeTasks.length === 0" class="empty-group">
              暂无运行中的任务
            </div>
          </div>
        </div>

        <!-- 未运行的任务 -->
        <div class="task-group">
          <div class="group-header" @click="showInactiveGroup = !showInactiveGroup">
            <span class="group-title">
              <span class="group-icon inactive">⏸</span>
              未运行 ({{ inactiveTasks.length }})
            </span>
            <span class="toggle-icon">{{ showInactiveGroup ? '▼' : '▶' }}</span>
          </div>
          
          <div v-if="showInactiveGroup" class="group-content">
            <div
              v-for="task in inactiveTasks"
              :key="task.id"
              class="task-card"
              :class="{ selected: selectedTaskId === task.id }"
              @click="selectedTaskId = task.id; loadDocuments()"
            >
              <div class="task-info">
                <h3>{{ task.name }}</h3>
                <div class="task-meta">
                  <span class="badge">{{ task.keywords?.length || 0 }} 关键词</span>
                  <span class="badge">{{ task.data_sources?.length || 0 }} 来源</span>
                </div>
              </div>
              
              <div class="task-actions">
                <button
                  @click.stop="handleStartTask(task)"
                  class="btn-icon"
                  title="启动任务"
                >
                  ▶
                </button>
                <button @click.stop="handleCopyTask(task)" class="btn-icon" title="复制配置">📋</button>
                <button @click.stop="handleEditTask(task)" class="btn-icon" title="编辑任务">✎</button>
                <button @click.stop="handleDeleteTask(task)" class="btn-icon danger" title="归档任务">📦</button>
                <button @click.stop="handlePermanentDelete(task)" class="btn-icon danger" title="删除任务">🗑️</button>
              </div>
            </div>
            
            <div v-if="inactiveTasks.length === 0" class="empty-group">
              暂无未运行的任务
            </div>
          </div>
        </div>

      <!-- 归档任务 -->
      <div class="archived-section">
        <div class="task-group">
          <div class="group-header" @click="showArchived = !showArchived">
            <span class="group-title">
              <span class="group-icon archived">📁</span>
              任务归档 ({{ archivedTasks.length }})
            </span>
            <span class="toggle-icon">{{ showArchived ? '▼' : '▶' }}</span>
          </div>
          
          <div v-if="showArchived" class="group-content">
            <div
              v-for="task in archivedTasks"
              :key="task.id"
              class="task-card archived"
              :class="{ selected: selectedTaskId === task.id }"
              @click="selectedTaskId = task.id; loadDocuments()"
            >
              <div class="task-info">
                <h3>{{ task.name }}</h3>
                <div class="task-meta">
                  <span class="badge">{{ task.keywords?.length || 0 }} 关键词</span>
                  <span class="badge archived-badge">已归档</span>
                </div>
              </div>
              
              <div class="task-actions">
                <button @click.stop="handleCopyTask(task)" class="btn-icon" title="复制配置">📋</button>
                <button @click.stop="handlePermanentDelete(task)" class="btn-icon danger" title="删除任务">🗑️</button>
              </div>
            </div>
            
            <div v-if="archivedTasks.length === 0" class="empty-group">
              暂无归档任务
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- 可拖拽分隔栏 -->
    <div 
      class="resizer" 
      @mousedown="startResize"
      title="拖动调整面板宽度"
    ></div>

    <!-- 右侧文献栏 -->
    <div class="documents-panel">
      <div class="panel-header">
        <h2>
          文献列表
          <span v-if="selectedTaskId && selectedTaskName" class="task-filter-badge">
            ({{ selectedTaskName }})
          </span>
        </h2>
        <div class="header-actions">
          <button @click="handleRefreshDocuments" class="btn-refresh" title="刷新文献列表">
            🔄
          </button>
        </div>
      </div>

      <!-- 筛选栏 -->
            <!-- 筛选栏 -->
      <div class="filters">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索标题或摘要..."
          class="search-input"
        />
        <select v-model="sourceFilter" class="filter-select">
          <option value="">全部来源</option>
          <option
            v-for="source in sources"
            :key="source"
            :value="source"
          >
            {{ source }}
          </option>
        </select>
        <select v-model="sortBy" class="filter-select">
          <option
            v-for="option in documentSortOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </div>

      <!-- 批量操作栏 -->
      <div class="batch-actions-bar">
        <div class="batch-select">
          <label class="checkbox-container">
            <input 
              type="checkbox" 
              :checked="isAllSelected" 
              @change="toggleSelectAll"
            />
            <span class="select-label">
              {{ isAllSelected ? '取消全选' : '全选当前页' }}
              <span v-if="hasSelection" class="selection-count">(已选 {{ selectedDocIds.size }})</span>
            </span>
          </label>
        </div>
        
        <div v-if="hasSelection" class="batch-buttons">
          <button @click="handleBatchDelete" class="btn-batch btn-delete">
            🗑️ 删除选中
          </button>
          <button @click="showExportDialog = true" class="btn-batch btn-export">
            📤 导出到Zotero
          </button>
        </div>
      </div>
      <!-- 文献列表 -->
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      <div v-else class="document-list">
        <div
          v-for="doc in paginatedDocuments"
          :key="doc.id"
          class="document-card"
          :class="{ 'doc-selected': selectedDocIds.has(doc.id) }"
        >
          <div class="doc-checkbox">
            <input 
              type="checkbox" 
              :checked="selectedDocIds.has(doc.id)" 
              @change="toggleSelectDoc(doc.id)"
            />
          </div>
          
          <div class="doc-content">
            <div class="doc-header">
              <div class="doc-title-row">
                <h3 class="doc-title">
                  <a v-if="doc.url" :href="doc.url" target="_blank" class="doc-link">
                    {{ doc.title }}
                  </a>
                  <span v-else>{{ doc.title }}</span>
                </h3>
                <span v-if="doc.relevance_score" class="score-badge">
                  {{ (doc.relevance_score * 100).toFixed(0) }}%
                </span>
              </div>
            </div>
            
            <div class="doc-meta">
              <span v-if="doc.authors" class="doc-authors">
                {{ formatAuthors(doc.authors) }}
              </span>
              <span class="doc-source">
                <span class="source-badge">{{ doc.source }}</span>
              </span>
              <span v-if="doc.published_at" class="doc-date" title="发表时间">
                发表: {{ formatDate(doc.published_at) }}
              </span>
              <span v-if="doc.created_at" class="doc-date" title="收录时间">
                收录: {{ formatDate(doc.created_at) }}
              </span>
            </div>
            
            <!-- AI生成的总结 -->
            <div v-if="doc.summary?.summary" class="doc-ai-summary">
              <div class="ai-summary-label">🤖 AI总结</div>
              <p class="ai-summary-content">{{ doc.summary.summary }}</p>
              <div v-if="doc.summary.highlights && doc.summary.highlights.length > 0" class="ai-highlights">
                <div class="highlights-label">✨ 关键亮点:</div>
                <ul class="highlights-list">
                  <li v-for="(highlight, idx) in doc.summary.highlights" :key="idx">
                    {{ highlight }}
                  </li>
                </ul>
              </div>
            </div>
            
            <!-- 原始摘要 -->
            <div v-if="doc.abstract" class="doc-abstract-container">
              <div v-if="doc.summary?.summary" class="abstract-label">📄 原始摘要</div>
              <p class="doc-abstract" :class="{ 'abstract-collapsed': !expandedAbstracts.has(doc.id) }">
                {{ doc.abstract }}
              </p>
              <button v-if="doc.abstract.length > 200" 
                      @click="toggleAbstract(doc.id)" 
                      class="btn-toggle-abstract">
                {{ expandedAbstracts.has(doc.id) ? '收起' : '展开摘要' }}
              </button>
            </div>
            
            <div v-if="doc.keywords?.length" class="doc-keywords">
              <span v-for="(kw, idx) in doc.keywords.slice(0, 8)" :key="idx" class="keyword-tag">
                {{ kw }}
              </span>
              <span v-if="doc.keywords.length > 8" class="keyword-more">+{{ doc.keywords.length - 8 }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="filteredDocuments.length === 0" class="empty-state">
          <div class="empty-icon">📄</div>
          <p>暂无文献数据</p>
          <p class="empty-hint">选择一个任务查看相关文献</p>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalFilteredPages > 1" class="pagination">
        <button
          @click="handlePageChange(currentPage - 1)"
          :disabled="currentPage === 1"
          class="btn-page"
        >
          上一页
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalFilteredPages }}</span>
        <button
          @click="handlePageChange(currentPage + 1)"
          :disabled="currentPage >= totalFilteredPages"
          class="btn-page"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 右侧可拖拽分隔栏 -->
    <div 
      class="resizer resizer-right" 
      @mousedown="startResizeRight"
      title="拖动调整图表面板宽度"
    ></div>

    <!-- 图表分析面板 -->
    <DocumentCharts :documents="filteredDocuments" :style="{ width: rightPanelWidth + 'px' }" />

    <!-- 任务表单弹窗 -->
    <TaskForm
      v-if="showTaskModal"
      :task="editingTask"
      @close="showTaskModal = false"
      @saved="handleTaskSaved"
    />

    <!-- 导出到Zotero对话框 -->
    <div v-if="showExportDialog" class="modal-overlay" @click.self="showExportDialog = false">
      <div class="modal-content export-dialog">
        <div class="modal-header">
          <h3>导出到Zotero</h3>
          <button class="btn-close" @click="showExportDialog = false">×</button>
        </div>
        
        <div class="modal-body">
          <p class="export-info">
            将选中的 <strong>{{ selectedDocIds.size }}</strong> 篇文献导出到Zotero集合:
          </p>
          
          <div class="form-group">
            <label for="collection-name">集合名称:</label>
            <input 
              id="collection-name"
              v-model="exportCollectionName" 
              type="text"
              placeholder="输入Zotero集合名称..."
              class="form-input"
              @keyup.enter="handleBatchExport"
            />
            <p class="form-hint">如果集合不存在,将自动创建</p>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="showExportDialog = false" class="btn-cancel">
            取消
          </button>
          <button 
            @click="handleBatchExport" 
            class="btn-primary"
            :disabled="!exportCollectionName.trim()"
          >
            确认导出
          </button>
        </div>
      </div>
    </div>

    <!-- 提示消息 -->
    <div v-if="showMessage" class="toast" :class="messageType">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { tasksApi } from '@/api/tasks'
import { documentsApi } from '@/api/documents'
import { analyticsApi } from '@/api/analytics'
import { documentSortOptions } from '@/config/static'
import TaskForm from '@/components/tasks/TaskForm.vue'
import DocumentCharts from '@/components/documents/DocumentCharts.vue'

const API_BASE_URL = 'http://localhost:6060'

interface Task {
  id: number
  name: string
  prompt: string
  keywords: (string | { keyword: string; is_user_defined: boolean })[]
  data_sources: (string | { source_name: string; parameters: any })[]
  run_at_hour: number
  run_at_minute?: number
  notification_config?: any
  status: string
  created_at: string
  updated_at: string
  // 新增配置项
  ai_config?: any
  filter_config?: any
  summary_config?: any
}

interface Document {
  id: number
  title: string
  authors?: string | string[]
  abstract?: string
  keywords?: string[]
  source: string  // 前端使用
  source_name?: string  // 后端返回
  relevance_score?: number  // 前端使用
  rank_score?: number  // 后端返回
  url?: string
  created_at: string
  published_at?: string
  summary?: {
    summary?: string
    highlights?: string[]
    research_trends?: string[]
  }
}

interface AnalyticsData {
  total_documents: number
  active_tasks: number
  documents_this_week: number
  avg_score: number
}

const tasks = ref<Task[]>([])
const archivedTasks = ref<Task[]>([])
const documents = ref<Document[]>([])
const analytics = ref<AnalyticsData | null>(null)
const loading = ref(false)
const showTaskModal = ref(false)
const editingTask = ref<Task | null>(null)
const searchQuery = ref('')
const sourceFilter = ref('')
const sortBy = ref(documentSortOptions[0]?.value ?? 'date')
const showArchived = ref(false)
const showActiveGroup = ref(true)
const showInactiveGroup = ref(true)
const selectedTaskId = ref<number | null>(null)

// 文献展开状态
const expandedAbstracts = ref<Set<number>>(new Set())

// 批量选择状态
const selectedDocIds = ref<Set<number>>(new Set())
const showExportDialog = ref(false)
const exportCollectionName = ref('')

// 面板拖拽
const leftPanelWidth = ref(400)
const rightPanelWidth = ref(320)
const isResizing = ref(false)
const isResizingRight = ref(false)

function startResize(e: MouseEvent) {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

function handleResize(e: MouseEvent) {
  if (!isResizing.value) return
  
  const minWidth = 300
  const maxWidth = 600
  const newWidth = Math.max(minWidth, Math.min(maxWidth, e.clientX))
  leftPanelWidth.value = newWidth
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// 右侧面板拖拽
function startResizeRight(e: MouseEvent) {
  isResizingRight.value = true
  document.addEventListener('mousemove', handleResizeRight)
  document.addEventListener('mouseup', stopResizeRight)
  e.preventDefault()
}

function handleResizeRight(e: MouseEvent) {
  if (!isResizingRight.value) return
  
  const minWidth = 280
  const maxWidth = 500
  const windowWidth = window.innerWidth
  const newWidth = Math.max(minWidth, Math.min(maxWidth, windowWidth - e.clientX))
  rightPanelWidth.value = newWidth
}

function stopResizeRight() {
  isResizingRight.value = false
  document.removeEventListener('mousemove', handleResizeRight)
  document.removeEventListener('mouseup', stopResizeRight)
}


// 提示消息
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const showMessage = ref(false)

const currentPage = ref(1)
const pageSize = ref(20)
const totalDocuments = ref(0)

// 分组任务
const activeTasks = computed(() => tasks.value.filter((t: any) => t.status === 'active'))
const inactiveTasks = computed(() => tasks.value.filter((t: any) => t.status === 'inactive'))

const filteredDocuments = computed(() => {
  let result = documents.value
  
  // 文本搜索
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(
      (doc: any) => 
        doc.title.toLowerCase().includes(query) ||
        doc.abstract?.toLowerCase().includes(query)
    )
  }
  
  // 来源筛选
  if (sourceFilter.value) {
    result = result.filter((doc: any) => doc.source === sourceFilter.value)
  }
  
  // 排序
  result = [...result].sort((a: any, b: any) => {
    if (sortBy.value === 'score') {
      return (b.relevance_score || 0) - (a.relevance_score || 0)
    } else if (sortBy.value === 'title') {
      return a.title.localeCompare(b.title, 'zh-CN')
    } else { // date
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    }
  })
  
  return result
})

// 分页后的文档列表
const paginatedDocuments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDocuments.value.slice(start, end)
})

// 基于过滤后的文档计算总页数
const totalFilteredPages = computed(() => {
  return Math.max(1, Math.ceil(filteredDocuments.value.length / pageSize.value))
})

const sources = computed(() => {
  const sourceSet = new Set(documents.value.map((doc: any) => doc.source))
  return Array.from(sourceSet)
})

const selectedTaskName = computed(() => {
  if (!selectedTaskId.value) return ''
  // 先在普通任务中查找
  let task = tasks.value.find((t: any) => t.id === selectedTaskId.value)
  // 如果没找到，在归档任务中查找
  if (!task) {
    task = archivedTasks.value.find((t: any) => t.id === selectedTaskId.value)
  }
  return task ? task.name : ''
})

// 批量选择计算属性
const isAllSelected = computed(() => {
  if (paginatedDocuments.value.length === 0) return false
  return paginatedDocuments.value.every((doc: Document) => selectedDocIds.value.has(doc.id))
})

const hasSelection = computed(() => selectedDocIds.value.size > 0)

// 监听筛选条件变化,重置页码
watch([searchQuery, sourceFilter, sortBy, selectedTaskId], () => {
  currentPage.value = 1
})

// 监听当前页码,确保不超出范围
watch(totalFilteredPages, (newTotal: number) => {
  if (currentPage.value > newTotal) {
    currentPage.value = Math.max(1, newTotal)
  }
})

// 辅助函数
function formatAuthors(authors: string | string[] | null | undefined): string {
  if (!authors) return '未知作者'
  
  // 如果已经是数组
  if (Array.isArray(authors)) {
    if (authors.length === 0) return '未知作者'
    if (authors.length <= 3) return authors.join(', ')
    return `${authors.slice(0, 3).join(', ')} 等 ${authors.length} 人`
  }
  
  // 如果是字符串
  const authorList = authors.split(',').map(a => a.trim())
  if (authorList.length <= 3) return authors
  return `${authorList.slice(0, 3).join(', ')} 等 ${authorList.length} 人`
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function toggleAbstract(docId: number) {
  if (expandedAbstracts.value.has(docId)) {
    expandedAbstracts.value.delete(docId)
  } else {
    expandedAbstracts.value.add(docId)
  }
  // 触发响应式更新
  expandedAbstracts.value = new Set(expandedAbstracts.value)
}

// 批量选择方法
function toggleSelectAll() {
  if (isAllSelected.value) {
    // 取消全选当前页
    paginatedDocuments.value.forEach((doc: Document) => {
      selectedDocIds.value.delete(doc.id)
    })
  } else {
    // 全选当前页
    paginatedDocuments.value.forEach((doc: Document) => {
      selectedDocIds.value.add(doc.id)
    })
  }
  selectedDocIds.value = new Set(selectedDocIds.value)
}

function toggleSelectDoc(docId: number) {
  if (selectedDocIds.value.has(docId)) {
    selectedDocIds.value.delete(docId)
  } else {
    selectedDocIds.value.add(docId)
  }
  selectedDocIds.value = new Set(selectedDocIds.value)
}

async function handleBatchDelete() {
  if (selectedDocIds.value.size === 0) {
    showToast('请先选择要删除的文献', 'error')
    return
  }

  if (!confirm(`确定删除选中的 ${selectedDocIds.value.size} 篇文献吗?\n删除后无法恢复!`)) {
    return
  }

  try {
    const token = localStorage.getItem('litea_auth_token')
    const response = await axios.post(`${API_BASE_URL}/api/documents/batch/delete`, {
      document_ids: Array.from(selectedDocIds.value)
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.success) {
      showToast(`成功删除 ${response.data.deleted} 篇文献`, 'success')
      selectedDocIds.value.clear()
      await loadDocuments()
    } else {
      showToast('删除失败', 'error')
    }
  } catch (error) {
    console.error('Batch delete failed:', error)
    showToast('删除失败', 'error')
  }
}

async function handleBatchExport() {
  if (!exportCollectionName.value.trim()) {
    showToast('请输入Zotero集合名称', 'error')
    return
  }

  if (selectedDocIds.value.size === 0) {
    showToast('请先选择要导出的文献', 'error')
    return
  }

  try {
    const token = localStorage.getItem('litea_auth_token')
    const response = await axios.post(`${API_BASE_URL}/api/documents/export/zotero`, {
      document_ids: Array.from(selectedDocIds.value),
      collection_name: exportCollectionName.value
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.data.data) {
      const exported = response.data.data.exported || 0
      showToast(`成功导出 ${exported} 篇文献到 "${exportCollectionName.value}"`, 'success')
      showExportDialog.value = false
      exportCollectionName.value = ''
      selectedDocIds.value.clear()
    } else {
      showToast('导出失败', 'error')
    }
  } catch (error) {
    console.error('Batch export failed:', error)
    showToast('导出失败', 'error')
  }
}

function showToast(msg: string, type: 'success' | 'error' = 'success') {
  message.value = msg
  messageType.value = type
  showMessage.value = true
  setTimeout(() => {
    showMessage.value = false
  }, 3000)
}

async function loadTasks() {
  try {
    const response = await tasksApi.list()
    tasks.value = response.data || []
  } catch (error) {
    console.error('Failed to load tasks:', error)
  }
}

async function loadArchivedTasks() {
  try {
    const response = await tasksApi.listArchived()
    archivedTasks.value = response.data || []
  } catch (error) {
    console.error('Failed to load archived tasks:', error)
  }
}

async function loadDocuments() {
  loading.value = true
  try {
    let response
    if (selectedTaskId.value) {
      // 加载特定任务的文献
      response = await documentsApi.listForTask(selectedTaskId.value, {
        limit: pageSize.value,
        offset: (currentPage.value - 1) * pageSize.value
      })
    } else {
      // 加载所有文献
      response = await documentsApi.list({
        limit: pageSize.value,
        offset: (currentPage.value - 1) * pageSize.value
      })
    }
    const rawDocs = response.data?.items || []
    console.log('原始文档数据:', rawDocs.length, rawDocs[0])
    // 映射后端字段到前端字段
    const normalizedDocs: Document[] = rawDocs.map((doc: any) => ({
      ...doc,
      source: doc.source_name || doc.source || '未知',
      relevance_score: doc.rank_score !== undefined ? doc.rank_score : doc.relevance_score
    }))
    documents.value = normalizedDocs
    console.log('映射后文档数据:', documents.value[0])
    totalDocuments.value = response.data?.total || 0
  } catch (error) {
    console.error('Failed to load documents:', error)
  } finally {
    loading.value = false
  }
}

async function loadAnalytics() {
  try {
    const response = await analyticsApi.getOverview()
    analytics.value = response.data || null
  } catch (error) {
    console.error('Failed to load analytics:', error)
  }
}

async function handleStartTask(task: Task) {
  try {
    await tasksApi.start(task.id)
    await loadTasks()
    showToast(`任务 "${task.name}" 已启动`)
  } catch (error) {
    console.error('Failed to start task:', error)
    showToast('启动任务失败', 'error')
  }
}

async function handleStopTask(task: Task) {
  try {
    await tasksApi.stop(task.id)
    await loadTasks()
    showToast(`任务 "${task.name}" 已停止`)
  } catch (error) {
    console.error('Failed to stop task:', error)
    showToast('停止任务失败', 'error')
  }
}

async function handleEditTask(task: Task) {
  editingTask.value = task
  showTaskModal.value = true
}

async function handleCopyTask(task: Task) {
  // 创建任务的副本 - 复制所有配置字段，不包含id等元数据
  // 这样TaskForm会将其当作新任务创建
  const taskCopy: any = {
    name: `${task.name} (副本)`,
    prompt: task.prompt,
    keywords: task.keywords,
    data_sources: task.data_sources || [],
    run_at_hour: task.run_at_hour,
    run_at_minute: task.run_at_minute || 0,
    notification_config: task.notification_config || {},
  }
  
  // 复制AI配置（如果存在）
  if (task.ai_config) {
    taskCopy.ai_config = { ...task.ai_config }
  }
  
  // 复制筛选配置（如果存在）
  if (task.filter_config) {
    taskCopy.filter_config = { ...task.filter_config }
  }
  
  // 复制总结配置（如果存在）
  if (task.summary_config) {
    taskCopy.summary_config = { ...task.summary_config }
  }
  
  // 不设置id和status，这样TaskForm会认为这是新任务
  editingTask.value = taskCopy as Task
  showTaskModal.value = true
  
  showToast('任务配置已复制，可以修改后创建新任务', 'success')
}

async function handleDeleteTask(task: Task) {
  if (!confirm(`确定要归档任务 "${task.name}"？\n\n归档后任务将移到"任务归档"区域，相关文献仍会保留，但任务无法再启动。`)) return
  
  try {
    await tasksApi.delete(task.id)
    await loadTasks()
    await loadArchivedTasks()
    await loadDocuments()
    showToast(`任务 "${task.name}" 已归档`)
  } catch (error) {
    console.error('Failed to archive task:', error)
    showToast('归档任务失败', 'error')
  }
}

async function handlePermanentDelete(task: Task) {
  if (!confirm(`确定要永久删除任务 "${task.name}"？\n\n任务及其关联的所有文献都将被永久删除，此操作不可恢复！`)) return
  
  try {
    await tasksApi.delete(task.id)
    await loadTasks()
    await loadArchivedTasks()
    // 如果删除的是当前选中的任务，清除选择
    if (selectedTaskId.value === task.id) {
      selectedTaskId.value = null
    }
    await loadDocuments()
    showToast(`任务 "${task.name}" 已永久删除`, 'success')
  } catch (error) {
    console.error('Failed to delete task:', error)
    showToast('删除任务失败', 'error')
  }
}

function handleCreateTask() {
  editingTask.value = null
  showTaskModal.value = true
}

async function handleTaskSaved() {
  showTaskModal.value = false
  // 判断是编辑还是创建：有editingTask且有id才是编辑
  const isEditing = editingTask.value !== null && (editingTask.value as any)?.id
  editingTask.value = null
  await loadTasks()
  await loadDocuments()
  showToast(isEditing ? '任务已更新' : '任务已创建')
}

async function handleRefreshDocuments() {
  await loadDocuments()
  await loadAnalytics()
  showToast('文献列表已刷新')
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadDocuments()
}

onMounted(() => {
  loadTasks()
  loadArchivedTasks()
  loadDocuments()
  loadAnalytics()
})
</script>

<style scoped>
.home-view {
  display: flex;
  height: calc(100vh - 60px);
  gap: 0;
  background: #f9fafb;
  position: relative;
}

.home-view.resizing {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* 左侧任务面板 */
.tasks-panel {
  background: white;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e5e7eb;
  flex-shrink: 0;
}

/* 可拖拽分隔栏 */
.resizer {
  width: 8px;
  background: #f3f4f6;
  cursor: col-resize;
  position: relative;
  flex-shrink: 0;
  transition: background 0.2s;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.resizer:hover {
  background: #d1d5db;
}

.resizer:active {
  background: #9ca3af;
}

.resizer::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 40px;
  background: #9ca3af;
  border-radius: 2px;
  pointer-events: none;
}

/* 右侧文献面板 */
.documents-panel {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  background: #3b82f6;
  border-bottom: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ffffff;
}

.task-filter-badge {
  font-size: 13px;
  font-weight: 500;
  color: white;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 10px;
  border-radius: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-create, .btn-toggle, .btn-refresh {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background: white;
  color: #3b82f6;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-create:hover, .btn-toggle:hover, .btn-refresh:hover {
  background: #f0f9ff;
  transform: translateY(-1px);
}

/* 任务列表 */
.task-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.task-card {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;
  cursor: pointer;
}

.task-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.task-card.active {
  border-color: #10b981;
  background: #f0fdf4;
}

.task-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.task-card.selected.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.task-info h3 {
  margin: 0 0 6px 0;
  font-size: 14px;
  font-weight: 600;
}

.task-meta {
  display: flex;
  gap: 6px;
}

.badge {
  padding: 2px 8px;
  background: #f3f4f6;
  border-radius: 12px;
  font-size: 12px;
  color: #6b7280;
}

.task-actions {
  display: flex;
  gap: 4px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.btn-icon:hover {
  background: #f9fafb;
}

.btn-icon.danger:hover {
  background: #fee2e2;
  border-color: #ef4444;
  color: #ef4444;
}

/* 归档任务区域 */
.archived-section {
  margin-top: 12px;
  border-top: 1px solid #e5e7eb;
  padding-top: 12px;
}

.task-card.archived {
  background: #f9fafb;
  border-color: #e5e7eb;
  opacity: 0.85;
}

.task-card.archived:hover {
  opacity: 1;
  background: #f3f4f6;
}

.task-card.archived.selected {
  background: #eff6ff;
  border-color: #3b82f6;
  opacity: 1;
}

.task-card.archived .task-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.task-card.archived:hover .task-actions {
  opacity: 1;
}

.archived-badge {
  background: #fee2e2;
  color: #dc2626;
}

/* 统计栏 */
.analytics-bar {
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.stat-card {
  flex: 1;
  padding: 12px;
  background: white;
  border-radius: 6px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

/* 过滤栏 */
.filters {
  padding: 12px 20px;
  display: flex;
  gap: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
}

.source-select {
  width: 160px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
}

/* 文献列表 */
.document-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px;
}

.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}

/* 批量操作栏 */
.batch-actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 12px;
}

.batch-select {
  display: flex;
  align-items: center;
}

.checkbox-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  gap: 8px;
}

.checkbox-container input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.select-label {
  font-size: 14px;
  color: #374151;
  user-select: none;
}

.selection-count {
  color: #3b82f6;
  font-weight: 600;
  margin-left: 4px;
}

.batch-buttons {
  display: flex;
  gap: 8px;
}

.btn-batch {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete {
  background: #fee;
  color: #dc2626;
}

.btn-delete:hover {
  background: #fdd;
}

.btn-export {
  background: #eff6ff;
  color: #2563eb;
}

.btn-export:hover {
  background: #dbeafe;
}

/* 文献卡片 */
.document-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.2s;
}

.document-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.document-card.doc-selected {
  background: #eff6ff;
  border-color: #3b82f6;
}

.doc-checkbox {
  flex-shrink: 0;
  padding-top: 2px;
}

.doc-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.doc-content {
  flex: 1;
  min-width: 0;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 8px;
}

.doc-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  flex: 1;
  line-height: 1.4;
}

.score {
  padding: 4px 8px;
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 12px;
}

.doc-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.source-badge {
  padding: 2px 8px;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 4px;
  font-size: 12px;
}

.doc-abstract {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  margin: 8px 0;
}

.doc-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.doc-abstract-container {
  margin: 10px 0;
}

/* AI生成的总结样式 */
.doc-ai-summary {
  margin: 12px 0;
  padding: 12px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 3px solid #3b82f6;
  border-radius: 6px;
}

.ai-summary-label {
  font-size: 12px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 6px;
}

.ai-summary-content {
  font-size: 13px;
  line-height: 1.6;
  color: #1f2937;
  margin: 0;
}

.ai-highlights {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #bfdbfe;
}

.highlights-label {
  font-size: 12px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 6px;
}

.highlights-list {
  margin: 0;
  padding-left: 20px;
  list-style: none;
}

.highlights-list li {
  font-size: 12px;
  line-height: 1.6;
  color: #374151;
  margin-bottom: 4px;
  position: relative;
}

.highlights-list li::before {
  content: "•";
  color: #3b82f6;
  font-weight: bold;
  position: absolute;
  left: -12px;
}

.abstract-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 6px;
}

.keyword-more {
  color: #9ca3af;
  font-size: 12px;
  padding: 4px 8px;
}

.keyword {
  padding: 3px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  color: #374151;
}

/* 分页 */
.pagination {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.btn-page {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.btn-page:hover:not(:disabled) {
  background: #f9fafb;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #6b7280;
}

/* Header actions */
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-refresh {
  width: 32px;
  height: 32px;
  padding: 4px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-refresh:hover {
  background: #f9fafb;
  transform: rotate(90deg);
  transition: all 0.3s;
}

/* Toast 提示 */
/* 导出对话框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: auto;
}

.export-dialog .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.export-dialog .modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.btn-close {
  background: none;
  border: none;
  font-size: 28px;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f3f4f6;
  color: #111827;
}

.modal-body {
  padding: 24px;
}

.export-info {
  margin: 0 0 20px 0;
  color: #374151;
  font-size: 14px;
  line-height: 1.5;
}

.export-info strong {
  color: #3b82f6;
  font-weight: 600;
}

.form-group {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-hint {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #6b7280;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.btn-cancel, .btn-primary {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

/* 提示消息 */
.toast {
  position: fixed;
  top: 80px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  font-weight: 500;
  z-index: 2000;
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  background: #10b981;
  color: white;
}

.toast.error {
  background: #ef4444;
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 任务分组 */
.task-group {
  margin-bottom: 12px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f9fafb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.group-header:hover {
  background: #f3f4f6;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #1f2937;
  font-size: 14px;
}

.group-icon {
  font-size: 16px;
}

.group-icon.running {
  color: #10b981;
}

.group-icon.inactive {
  color: #6b7280;
}

.group-icon.archived {
  color: #9ca3af;
}

.group-content {
  margin-top: 8px;
  animation: fadeIn 0.2s ease-out;
}

.empty-group {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
  background: #f9fafb;
  border-radius: 6px;
  margin-top: 8px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== 文献卡片优化样式 ===== */
.document-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.document-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.document-card.expanded {
  border-color: #3b82f6;
  background: #f9fafb;
}

.doc-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}

.doc-title {
  flex: 1;
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
  color: #1f2937;
}

.doc-link {
  color: #3b82f6;
  text-decoration: none;
  transition: color 0.2s;
}

.doc-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

.doc-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.score-badge {
  background: #10b981;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.doc-authors, .doc-source, .doc-date {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6b7280;
}

.doc-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  font-size: 13px;
  color: #6b7280;
}

.source-badge {
  background: #e5e7eb;
  color: #374151;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.doc-abstract-container {
  margin: 12px 0;
}

.doc-abstract {
  font-size: 14px;
  line-height: 1.6;
  color: #4b5563;
  margin: 0 0 8px 0;
}

.doc-abstract.abstract-collapsed {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.btn-toggle-abstract {
  font-size: 12px;
  color: #3b82f6;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-toggle-abstract:hover {
  background: #eff6ff;
}

.keyword-tag {
  background: #f3f4f6;
  color: #374151;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid #e5e7eb;
  transition: all 0.2s;
}

.keyword-tag:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.keyword-more {
  color: #9ca3af;
  font-size: 12px;
  padding: 4px 8px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #9ca3af;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  color: #3b82f6;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.filters {
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 180px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  cursor: pointer;
  min-width: 120px;
  transition: border-color 0.2s;
}

.filter-select:hover {
  border-color: #3b82f6;
}
</style>
