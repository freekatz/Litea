<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Back Button -->
    <router-link to="/tasks" class="inline-flex items-center text-gray-600 hover:text-gray-900">
      <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      返回任务列表
    </router-link>

    <!-- Loading State -->
    <LoadingSpinner v-if="loading" message="加载任务详情..." />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Task Detail -->
    <div v-else-if="task" class="space-y-6">
      <!-- Header -->
      <div class="card">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h1 class="text-3xl font-serif font-bold text-gray-900">
                {{ task.name }}
              </h1>
              <span
                class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                :class="statusColors[task.status]"
              >
                {{ statusText[task.status] }}
              </span>
            </div>
            <p class="text-gray-600">{{ task.prompt }}</p>
          </div>
          <div class="flex items-center gap-2">
            <!-- 启动定时任务 (仅在 inactive 状态显示) -->
            <button
              v-if="task.status === 'inactive'"
              @click="startTask"
              class="btn bg-green-600 text-white hover:bg-green-700"
              title="启动定时任务,按计划自动执行"
            >
              <svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              启动定时任务
            </button>

            <!-- 停止定时任务 (仅在 active 状态显示) -->
            <button
              v-if="task.status === 'active'"
              @click="stopTask"
              class="btn bg-red-600 text-white hover:bg-red-700"
              title="停止定时任务"
            >
              <svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
              </svg>
              停止定时任务
            </button>

            <!-- 编辑 -->
            <router-link :to="`/tasks/${task.id}/edit`" class="btn btn-secondary">
              <svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              编辑
            </router-link>

            <!-- 删除 -->
            <button
              @click="confirmDelete"
              class="btn bg-red-600 text-white hover:bg-red-700"
              title="删除任务及其关联文献"
            >
              <svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              删除
            </button>
          </div>
        </div>
      </div>

      <!-- Task Info Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="card">
          <div class="text-sm font-medium text-gray-500 mb-1">关键词数量</div>
          <div class="text-2xl font-bold text-gray-900">{{ task.keywords.length }}</div>
        </div>
        <div class="card">
          <div class="text-sm font-medium text-gray-500 mb-1">数据来源</div>
          <div class="text-2xl font-bold text-gray-900">{{ task.sources.length }}</div>
        </div>
        <div class="card">
          <div class="text-sm font-medium text-gray-500 mb-1">检索文献</div>
          <div class="text-2xl font-bold text-gray-900">{{ documentCount }}</div>
        </div>
        <div class="card">
          <div class="text-sm font-medium text-gray-500 mb-1">执行时间</div>
          <div class="text-2xl font-bold text-gray-900">
            {{ task.run_at_hour !== null && task.run_at_hour !== undefined 
              ? `${String(task.run_at_hour).padStart(2, '0')}:${String(task.run_at_minute || 0).padStart(2, '0')}` 
              : '-' }}
          </div>
        </div>
      </div>

      <!-- Schedule Info (if task is active) -->
      <div v-if="task.status === 'active' && task.next_run_at" class="card bg-blue-50 border-blue-200">
        <div class="flex items-start">
          <svg class="w-6 h-6 text-blue-600 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div class="flex-1">
            <h3 class="text-sm font-semibold text-blue-900 mb-1">定时任务已启动</h3>
            <p class="text-sm text-blue-800">
              <span v-if="task.last_run_at">上次执行：{{ formatDateTime(task.last_run_at) }}</span>
              <span v-if="task.last_run_at && task.next_run_at" class="mx-2">•</span>
              <span v-if="task.next_run_at">下次执行：{{ formatDateTime(task.next_run_at) }}</span>
            </p>
          </div>
        </div>
      </div>

      <!-- Task Configuration (Editable) -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-serif font-semibold text-gray-900">任务配置</h2>
          <button
            v-if="!isEditing"
            @click="startEditing"
            class="text-sm text-primary-600 hover:text-primary-700"
          >
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            编辑配置
          </button>
        </div>

        <div v-if="!isEditing" class="space-y-4">
          <!-- View Mode -->
          <div>
            <label class="text-sm font-medium text-gray-500">每日执行时间</label>
            <div class="mt-1 text-gray-900">
              {{ task.run_at_hour !== null && task.run_at_hour !== undefined 
                ? `${String(task.run_at_hour).padStart(2, '0')}:${String(task.run_at_minute || 0).padStart(2, '0')}` 
                : '未设置' }}
            </div>
          </div>

          <div>
            <label class="text-sm font-medium text-gray-500">通知设置</label>
            <div class="mt-1 text-gray-900">
              {{ task.notification?.channel === 'email' ? `邮箱: ${task.notification.recipients?.[0] || '未设置'}` : '未启用' }}
            </div>
          </div>
        </div>

        <div v-else class="space-y-4">
          <!-- Edit Mode -->
          <div>
            <label class="text-sm font-medium text-gray-700">每日执行时间</label>
            <div class="flex items-center gap-4 mt-2">
              <input
                v-model.number="editConfig.run_at_hour"
                type="number"
                min="0"
                max="23"
                class="input w-24"
                placeholder="9"
              />
              <span class="text-sm text-gray-600">时</span>
              <input
                v-model.number="editConfig.run_at_minute"
                type="number"
                min="0"
                max="59"
                class="input w-24"
                placeholder="0"
              />
              <span class="text-sm text-gray-600">分</span>
            </div>
          </div>

          <div>
            <label class="text-sm font-medium text-gray-700">通知邮箱</label>
            <input
              v-model="editConfig.email"
              type="email"
              class="input mt-2"
              placeholder="your-email@example.com"
            />
            <p class="mt-1 text-xs text-gray-500">留空则不发送邮件通知</p>
          </div>

          <div class="flex items-center gap-2 pt-2">
            <button
              @click="saveConfig(false)"
              :disabled="saving"
              class="btn btn-secondary"
            >
              {{ saving ? '保存中...' : '保存' }}
            </button>
            <button
              v-if="task.status === 'inactive'"
              @click="saveConfig(true)"
              :disabled="saving"
              class="btn btn-primary"
            >
              {{ saving ? '保存中...' : '保存并启动' }}
            </button>
            <button
              @click="cancelEditing"
              class="btn btn-secondary"
            >
              取消
            </button>
            <p class="text-xs text-gray-500 ml-2">
              {{ task.status === 'active' ? '保存后将自动重启任务并立即执行一次' : '保存配置' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Keywords -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">检索关键词</h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="keyword in task.keywords"
            :key="keyword"
            class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800"
          >
            {{ keyword }}
          </span>
        </div>
      </div>

      <!-- Sources -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">数据来源</h2>
        <div class="space-y-2">
          <div
            v-for="source in task.sources"
            :key="source"
            class="flex items-center p-3 bg-gray-50 rounded-lg"
          >
            <svg class="w-5 h-5 text-primary-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="font-medium text-gray-900">{{ sourceNames[source] || source }}</span>
          </div>
        </div>
      </div>

      <!-- Old Schedule Config - Hidden for simplified design -->
      <div v-if="false" class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">定时执行</h2>
        <div v-if="task.schedule_config?.enabled || task.schedule_cron" class="space-y-3">
          <div class="flex items-center text-gray-700">
            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            频率: {{ task.schedule_config?.frequency ? frequencyText[task.schedule_config.frequency] : '自定义' }}
          </div>
          <div class="flex items-center text-gray-700">
            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            执行时间: {{ task.schedule_config?.time || (task.run_at_hour !== undefined ? `${task.run_at_hour}:00` : '未设置') }}
          </div>
          <div v-if="task.next_run_at" class="flex items-center text-gray-700">
            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            下次运行: {{ formatDate(task.next_run_at) }}
          </div>
        </div>
        <div v-else class="text-gray-500">
          定时任务未启用
        </div>
      </div>

      <!-- Notification Config -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">通知设置</h2>
        <div v-if="task.notification_config?.enabled || task.notification" class="space-y-3">
          <div class="flex items-center text-gray-700">
            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            推送渠道: {{ task.notification_config?.channels?.join(', ') || '邮件' }}
          </div>
          <div v-if="task.notification_config?.email || task.notification?.email" class="flex items-center text-gray-700">
            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            邮箱: {{ task.notification_config?.email || task.notification?.email }}
          </div>
        </div>
        <div v-else class="text-gray-500">
          通知推送未启用
        </div>
      </div>

      <!-- Execution History -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-serif font-semibold text-gray-900">执行历史</h2>
          <span class="text-sm text-gray-500">
            上次执行: {{ task.last_run_at ? formatRelativeTime(task.last_run_at) : '从未运行' }}
          </span>
        </div>
        <div class="text-gray-500 text-center py-8">
          执行历史记录功能开发中...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTaskStore } from '@/stores/task'
import { useDocumentStore } from '@/stores/document'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import { formatDate, formatRelativeTime } from '@/utils/helpers'
import { showToast } from '@/utils/toast'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()
const documentStore = useDocumentStore()

const taskId = computed(() => Number(route.params.id))
const loading = ref(false)
const error = ref('')
const task = computed(() => taskStore.tasks.find(t => t.id === taskId.value))
const documentCount = ref(0)

// Config editing state
const isEditing = ref(false)
const saving = ref(false)
const editConfig = ref({
  run_at_hour: 9,
  run_at_minute: 0,
  email: ''
})

const statusColors = {
  inactive: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800'
}

const statusText = {
  inactive: '未运行',
  active: '运行中'
}

const sourceNames: Record<string, string> = {
  arxiv: 'arXiv',
  pubmed: 'PubMed',
  semantic_scholar: 'Semantic Scholar'
}

const frequencyText = {
  daily: '每天',
  weekly: '每周',
  monthly: '每月'
}

onMounted(async () => {
  await loadTaskDetail()
})

async function loadTaskDetail() {
  loading.value = true
  error.value = ''
  
  try {
    // Ensure task is loaded
    if (!task.value) {
      await taskStore.fetchTasks()
    }
    
    // Load document count for this task
    await documentStore.fetchDocuments({ task_id: taskId.value, page_size: 1 })
    documentCount.value = documentStore.total
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载任务详情失败'
  } finally {
    loading.value = false
  }
}

async function startTask() {
  if (!confirm('确认启动定时任务？任务将立即执行一次，之后每天按设定时间自动执行。')) {
    return
  }
  try {
    await taskStore.startTask(taskId.value)
    showToast('定时任务已启动，正在执行首次检索...', 'success')
    await loadTaskDetail()
  } catch (e: any) {
    showToast(e.response?.data?.detail || '启动定时任务失败', 'error')
  }
}

async function stopTask() {
  if (!confirm('确认停止定时任务？')) {
    return
  }
  try {
    await taskStore.stopTask(taskId.value)
    showToast('定时任务已停止', 'success')
    await loadTaskDetail()
  } catch (e: any) {
    showToast(e.response?.data?.detail || '停止任务失败', 'error')
  }
}

async function confirmDelete() {
  if (!task.value) return
  
  const confirmed = confirm(
    `确定要删除任务「${task.value.name}」吗？\n\n任务及其关联的所有文献都将被永久删除，此操作不可恢复。`
  )
  
  if (!confirmed) return
  
  try {
    await taskStore.deleteTask(taskId.value)
    showToast('任务已删除', 'success')
    router.push('/tasks')
  } catch (e: any) {
    showToast(e.response?.data?.detail || '删除任务失败', 'error')
  }
}

function startEditing() {
  if (!task.value) return
  
  isEditing.value = true
  editConfig.value = {
    run_at_hour: task.value.run_at_hour ?? 9,
    run_at_minute: task.value.run_at_minute ?? 0,
    email: task.value.notification?.recipients?.[0] || ''
  }
}

function cancelEditing() {
  isEditing.value = false
}

async function saveConfig(startAfterSave = false) {
  if (!task.value) return
  
  // Validate
  if (editConfig.value.run_at_hour < 0 || editConfig.value.run_at_hour > 23) {
    showToast('小时必须在 0-23 之间', 'error')
    return
  }
  
  if (editConfig.value.run_at_minute < 0 || editConfig.value.run_at_minute > 59) {
    showToast('分钟必须在 0-59 之间', 'error')
    return
  }
  
  saving.value = true
  try {
    const config = {
      run_at_hour: editConfig.value.run_at_hour,
      run_at_minute: editConfig.value.run_at_minute,
      notification_config: {
        channel: editConfig.value.email ? 'email' : '',
        recipients: editConfig.value.email ? [editConfig.value.email] : [],
        schedule: null,
        options: {}
      }
    }
    
    const wasActive = task.value.status === 'active'
    
    // Always use restart to update config
    // For active tasks: it will restart automatically
    // For inactive tasks: it will just update config
    await taskStore.restartTask(taskId.value, config)
    
    if (wasActive) {
      showToast('配置已保存，任务正在重新启动并执行首次检索...', 'success', 4000)
    } else if (startAfterSave) {
      // If user wants to start after save and task was inactive
      await taskStore.startTask(taskId.value)
      showToast('配置已保存并启动，正在执行首次检索...', 'success', 4000)
    } else {
      showToast('配置已保存', 'success')
    }
    
    isEditing.value = false
    await loadTaskDetail()
  } catch (e: any) {
    showToast(e.response?.data?.detail || e.response?.data?.error || '保存配置失败', 'error')
  } finally {
    saving.value = false
  }
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffHours = Math.round(diffMs / (1000 * 60 * 60))
  
  // Format: YYYY-MM-DD HH:mm
  const formatted = date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
  
  // Add relative time hint
  if (Math.abs(diffHours) < 24) {
    if (diffHours > 0) {
      return `${formatted} (${diffHours}小时后)`
    } else if (diffHours < 0) {
      return `${formatted} (${Math.abs(diffHours)}小时前)`
    } else {
      return `${formatted} (即将执行)`
    }
  }
  
  return formatted
}

</script>
