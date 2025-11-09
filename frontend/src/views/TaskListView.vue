<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-serif font-bold text-gray-900">任务管理</h1>
        <p class="mt-2 text-sm text-gray-600">
          管理您的文献检索任务，配置自动推送
        </p>
      </div>
      <router-link to="/tasks/new" class="btn btn-primary">
        <svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        创建任务
      </router-link>
    </div>

    <!-- Filters -->
    <div class="card">
      <div class="flex items-center space-x-4">
        <div class="flex-1">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索任务名称或 Prompt..."
            class="input"
          />
        </div>
        <select v-model="statusFilter" class="input w-48">
          <option value="">所有状态</option>
          <option value="active">活跃</option>
          <option value="paused">暂停</option>
          <option value="archived">归档</option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <LoadingSpinner v-if="loading" message="加载任务列表..." />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Empty State -->
    <div v-else-if="filteredTasks.length === 0" class="card text-center py-12">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">暂无任务</h3>
      <p class="mt-1 text-sm text-gray-500">开始创建您的第一个文献检索任务</p>
      <div class="mt-6">
        <router-link to="/tasks/new" class="btn btn-primary">
          创建任务
        </router-link>
      </div>
    </div>

    <!-- Task List -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="card hover:shadow-md transition-shadow cursor-pointer"
        @click="$router.push(`/tasks/${task.id}`)"
      >
        <!-- Status Badge -->
        <div class="flex items-start justify-between mb-4">
          <span
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
            :class="statusColors[task.status]"
          >
            {{ statusText[task.status] }}
          </span>
          <div class="flex items-center space-x-2" @click.stop>
            <!-- 启动定时任务 (仅 inactive 状态) -->
            <button
              v-if="task.status === 'inactive'"
              @click="startTask(task.id)"
              class="p-1 text-green-400 hover:text-green-600 rounded"
              title="启动定时任务"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              </svg>
            </button>
            
            <!-- 停止定时任务 (仅 active 状态) -->
            <button
              v-if="task.status === 'active'"
              @click="stopTask(task.id)"
              class="p-1 text-red-400 hover:text-red-600 rounded"
              title="停止定时任务"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
              </svg>
            </button>

            <!-- 编辑 -->
            <router-link
              :to="`/tasks/${task.id}/edit`"
              class="p-1 text-gray-400 hover:text-primary-600 rounded"
              title="编辑"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </router-link>
            
            <!-- 删除 -->
            <button
              @click="confirmDelete(task)"
              class="p-1 text-gray-400 hover:text-red-600 rounded"
              title="删除"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Task Info -->
        <h3 class="text-lg font-serif font-semibold text-gray-900 mb-2">
          {{ task.name }}
        </h3>
        <p class="text-sm text-gray-600 mb-4 line-clamp-2">
          {{ task.prompt }}
        </p>

        <!-- Keywords -->
        <div class="flex flex-wrap gap-1 mb-4">
          <span
            v-for="keyword in task.keywords.slice(0, 5)"
            :key="keyword"
            class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
          >
            {{ keyword }}
          </span>
          <span
            v-if="task.keywords.length > 5"
            class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
          >
            +{{ task.keywords.length - 5 }}
          </span>
        </div>

        <!-- Meta Info -->
        <div class="text-xs text-gray-500 space-y-1">
          <div class="flex items-center">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span v-if="task.last_run_at">
              上次运行: {{ formatRelativeTime(task.last_run_at) }}
            </span>
            <span v-else>从未运行</span>
          </div>
          <div v-if="task.schedule_config?.enabled || task.schedule_cron" class="flex items-center">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span v-if="task.next_run_at">
              下次运行: {{ formatDate(task.next_run_at) }}
            </span>
            <span v-else>定时任务已启用</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <Modal
      v-model="deleteModal.show"
      title="删除任务"
      :content="`确定要删除任务「${deleteModal.task?.name}」吗？任务及其关联的所有文献都将被永久删除，此操作不可恢复。`"
      icon
      icon-type="danger"
      confirm-text="删除"
      @confirm="handleDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '@/stores/task'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import Modal from '@/components/Modal.vue'
import { formatDate, formatRelativeTime } from '@/utils/helpers'
import { showToast } from '@/utils/toast'
import type { Task } from '@/types'

const router = useRouter()
const taskStore = useTaskStore()

const searchQuery = ref('')
const statusFilter = ref('')
const deleteModal = ref<{ show: boolean; task: Task | null }>({
  show: false,
  task: null
})

const loading = computed(() => taskStore.loading)
const error = computed(() => taskStore.error)

const filteredTasks = computed(() => {
  let tasks = taskStore.tasks

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    tasks = tasks.filter(
      (task: Task) =>
        task.name.toLowerCase().includes(query) ||
        task.prompt.toLowerCase().includes(query)
    )
  }

  if (statusFilter.value) {
    tasks = tasks.filter((task: Task) => task.status === statusFilter.value)
  }

  return tasks
})

const statusColors = {
  inactive: 'bg-gray-100 text-gray-800',
  active: 'bg-green-100 text-green-800'
}

const statusText = {
  inactive: '未运行',
  active: '运行中'
}

onMounted(async () => {
  await taskStore.fetchTasks()
})

async function startTask(taskId: number) {
  try {
    await taskStore.startTask(taskId)
    showToast('定时任务已启动', 'success')
    await taskStore.fetchTasks()
  } catch (e) {
    showToast('启动定时任务失败', 'error')
  }
}

async function stopTask(taskId: number) {
  try {
    await taskStore.stopTask(taskId)
    showToast('定时任务已停止', 'success')
    await taskStore.fetchTasks()
  } catch (e) {
    showToast('停止任务失败', 'error')
  }
}

function confirmDelete(task: Task) {
  deleteModal.value = { show: true, task }
}

async function handleDelete() {
  if (!deleteModal.value.task) return
  
  try {
    await taskStore.deleteTask(deleteModal.value.task.id)
    showToast('任务已删除', 'success')
    deleteModal.value = { show: false, task: null }
  } catch (e) {
    showToast('删除任务失败', 'error')
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
</style>
