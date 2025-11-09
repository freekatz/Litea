<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-serif font-bold text-gray-900">
          {{ isEdit ? '编辑任务' : '创建任务' }}
        </h1>
        <p class="mt-2 text-sm text-gray-600">
          {{ isEdit ? '修改任务配置和参数' : '配置文献检索任务和推送设置' }}
        </p>
      </div>
      <router-link to="/tasks" class="text-gray-600 hover:text-gray-900">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </router-link>
    </div>

    <!-- Loading State -->
    <LoadingSpinner v-if="loading" message="加载任务信息..." />

    <!-- Error State -->
    <ErrorAlert v-else-if="error" :message="error" />

    <!-- Form -->
    <form v-else @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Basic Info -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">基本信息</h2>
        
        <div class="space-y-4">
          <div>
            <label class="label">任务名称 *</label>
            <input
              v-model="formData.name"
              type="text"
              required
              placeholder="例如: AI 领域最新论文追踪"
              class="input"
            />
          </div>

          <div>
            <label class="label">任务 Prompt *</label>
            <textarea
              v-model="formData.prompt"
              required
              rows="4"
              placeholder="描述您要检索的文献内容，例如: 检索人工智能和机器学习领域的最新研究成果，重点关注深度学习、自然语言处理和计算机视觉方向"
              class="input"
            />
            <p class="mt-1 text-sm text-gray-500">
              系统将基于此 Prompt 自动提取检索关键词
            </p>
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="label">检索关键词 *</label>
              <button
                type="button"
                @click="extractKeywords"
                :disabled="!formData.prompt || extracting"
                class="text-sm text-primary-600 hover:text-primary-700 disabled:text-gray-400 disabled:cursor-not-allowed"
              >
                <svg v-if="extracting" class="inline w-4 h-4 mr-1 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {{ extracting ? 'AI 提取中...' : '🤖 AI 提取关键词' }}
              </button>
            </div>
            <div class="flex flex-wrap gap-2 mb-2">
              <span
                v-for="(keyword, index) in formData.keywords"
                :key="index"
                class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800"
              >
                {{ keyword }}
                <button
                  type="button"
                  @click="removeKeyword(index)"
                  class="ml-2 text-primary-600 hover:text-primary-800"
                >
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </button>
              </span>
            </div>
            <div class="flex gap-2">
              <input
                v-model="newKeyword"
                type="text"
                placeholder="输入关键词后按回车添加"
                @keypress.enter.prevent="addKeyword"
                class="input flex-1"
              />
              <button
                type="button"
                @click="addKeyword"
                class="btn btn-secondary"
              >
                添加
              </button>
            </div>
          </div>

          <div>
            <label class="label">状态</label>
            <select v-model="formData.status" class="input">
              <option value="active">活跃</option>
              <option value="paused">暂停</option>
              <option value="archived">归档</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Data Sources -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">数据来源</h2>
        
        <div class="space-y-3">
          <div
            v-for="source in availableSources"
            :key="source.name"
            class="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
          >
            <div class="flex items-center">
              <input
                type="checkbox"
                :id="source.name"
                :checked="isSourceEnabled(source.name)"
                @change="toggleSource(source.name)"
                class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              />
              <label :for="source.name" class="ml-3">
                <div class="font-medium text-gray-900">{{ source.display_name }}</div>
                <div class="text-sm text-gray-500">{{ source.description }}</div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Schedule Config -->
      <div class="card">
        <h2 class="text-lg font-serif font-semibold text-gray-900 mb-4">定时执行</h2>

        <div class="space-y-4">
          <div>
            <label class="label">每日执行时间</label>
            <div class="flex items-center gap-4">
              <input
                v-model.number="formData.schedule_config.hour"
                type="number"
                min="0"
                max="23"
                class="input w-24"
                placeholder="9"
              />
              <span class="text-sm text-gray-600">时</span>
              <input
                v-model.number="formData.schedule_config.minute"
                type="number"
                min="0"
                max="59"
                class="input w-24"
                placeholder="0"
              />
              <span class="text-sm text-gray-600">分</span>
            </div>
            <p class="mt-1 text-sm text-gray-500">
              任务将在每天的这个时间点自动执行（Asia/Shanghai 时区）
            </p>
          </div>
        </div>
      </div>

      <!-- Notification Config -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-serif font-semibold text-gray-900">通知设置</h2>
          <label class="flex items-center cursor-pointer">
            <input
              v-model="formData.notification_config.enabled"
              type="checkbox"
              class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <span class="ml-2 text-sm text-gray-700">启用推送通知</span>
          </label>
        </div>

        <div v-if="formData.notification_config.enabled" class="space-y-4">
          <div>
            <label class="label">推送渠道</label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  v-model="formData.notification_config.channels"
                  type="checkbox"
                  value="email"
                  class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span class="ml-2 text-sm text-gray-700">邮件</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="formData.notification_config.channels"
                  type="checkbox"
                  value="wechat"
                  class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span class="ml-2 text-sm text-gray-700">微信</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="formData.notification_config.channels"
                  type="checkbox"
                  value="webhook"
                  class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span class="ml-2 text-sm text-gray-700">Webhook</span>
              </label>
            </div>
          </div>

          <div v-if="formData.notification_config.channels.includes('email')">
            <label class="label">接收邮箱</label>
            <input
              v-model="formData.notification_config.email"
              type="email"
              placeholder="your@email.com"
              class="input"
            />
          </div>

          <div v-if="formData.notification_config.channels.includes('wechat')">
            <label class="label">企业微信 Webhook URL</label>
            <input
              v-model="formData.notification_config.wechat_webhook"
              type="url"
              placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
              class="input"
            />
          </div>

          <div v-if="formData.notification_config.channels.includes('webhook')">
            <label class="label">自定义 Webhook URL</label>
            <input
              v-model="formData.notification_config.webhook_url"
              type="url"
              placeholder="https://your-webhook.com/notify"
              class="input"
            />
          </div>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="flex justify-end gap-3">
        <router-link to="/tasks" class="btn btn-secondary">
          取消
        </router-link>
        <button
          v-if="!isEdit"
          type="button"
          @click="handleSubmit(false)"
          :disabled="submitting"
          class="btn bg-blue-600 text-white hover:bg-blue-700"
        >
          {{ submitting ? '创建中...' : '创建任务' }}
        </button>
        <button
          type="button"
          @click="handleSubmit(true)"
          :disabled="submitting"
          class="btn btn-primary"
        >
          {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '创建并启动') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTaskStore } from '@/stores/task'
import { tasksApi } from '@/api/tasks'
import { sourcesApi } from '@/api/sources'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import ErrorAlert from '@/components/ErrorAlert.vue'
import { showToast } from '@/utils/toast'
import type { TaskFormData, RetrievalSource } from '@/types'

const router = useRouter()
const route = useRoute()
const taskStore = useTaskStore()

const isEdit = computed(() => !!route.params.id)
const taskId = computed(() => Number(route.params.id))

const loading = ref(false)
const error = ref('')
const submitting = ref(false)
const extracting = ref(false)
const newKeyword = ref('')
const availableSources = ref<RetrievalSource[]>([])

const formData = ref<TaskFormData & { status?: string }>({
  name: '',
  prompt: '',
  keywords: [],
  sources: [],
  schedule_config: {
    hour: 9,
    minute: 0
  },
  notification_config: {
    enabled: false,
    channels: [],
    email: '',
    wechat_webhook: '',
    webhook_url: ''
  },
  status: 'inactive'
})

onMounted(async () => {
  await loadSources()
  if (isEdit.value) {
    await loadTask()
  }
})

async function loadSources() {
  try {
    availableSources.value = await sourcesApi.list()
  } catch (e) {
    console.error('Failed to load sources:', e)
  }
}

async function loadTask() {
  loading.value = true
  error.value = ''
  try {
    const task = await tasksApi.get(taskId.value)
    
    // Transform backend data to form format
    formData.value = {
      name: task.name,
      prompt: task.prompt,
      keywords: Array.isArray(task.keywords) 
        ? task.keywords.map((k: any) => typeof k === 'string' ? k : k.keyword)
        : [],
      sources: Array.isArray(task.sources)
        ? task.sources.map((s: any) => typeof s === 'string' ? s : s.source_name)
        : [],
      schedule_config: {
        hour: task.run_at_hour ?? 9,
        minute: task.run_at_minute ?? 0
      },
      notification_config: {
        enabled: task.notification?.channel === 'email',
        channels: task.notification?.channel ? [task.notification.channel] : [],
        email: task.notification?.recipients?.[0] || '',
        wechat_webhook: '',
        webhook_url: ''
      },
      status: task.status
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载任务失败'
  } finally {
    loading.value = false
  }
}

async function extractKeywords() {
  if (!formData.value.prompt) return
  
  extracting.value = true
  try {
    const keywords = await tasksApi.extractKeywords(formData.value.prompt)
    formData.value.keywords = keywords
    showToast('关键词提取成功', 'success')
  } catch (e: any) {
    showToast(e.response?.data?.detail || 'AI 关键词提取失败', 'error')
  } finally {
    extracting.value = false
  }
}

function addKeyword() {
  const keyword = newKeyword.value.trim()
  if (keyword && !formData.value.keywords.includes(keyword)) {
    formData.value.keywords.push(keyword)
    newKeyword.value = ''
  }
}

function removeKeyword(index: number) {
  formData.value.keywords.splice(index, 1)
}

function isSourceEnabled(sourceName: string) {
  return formData.value.sources.includes(sourceName)
}

function toggleSource(sourceName: string) {
  const index = formData.value.sources.indexOf(sourceName)
  if (index > -1) {
    formData.value.sources.splice(index, 1)
  } else {
    formData.value.sources.push(sourceName)
  }
}

async function handleSubmit(startAfterCreate = false) {
  if (formData.value.keywords.length === 0) {
    alert('请至少添加一个检索关键词')
    return
  }
  if (formData.value.sources.length === 0) {
    alert('请至少选择一个数据来源')
    return
  }

  submitting.value = true
  try {
    const { status, ...taskData } = formData.value
    
    // Deduplicate keywords (case-insensitive)
    const uniqueKeywords = Array.from(new Set(taskData.keywords.map((k: string) => k.toLowerCase())))
      .map(lower => taskData.keywords.find((k: string) => k.toLowerCase() === lower)!)
    
    // Transform data to match backend schema
    const payload = {
      ...taskData,
      keywords: uniqueKeywords.map((k: string) => ({ keyword: k, is_user_defined: true })),
      sources: taskData.sources.map((s: string) => ({ source_name: s, parameters: {} })),
      notification: {
        channel: taskData.notification_config.enabled ? 'email' : '',
        recipients: taskData.notification_config.email ? [taskData.notification_config.email] : [],
        schedule: null,
        options: {}
      },
      run_at_hour: taskData.schedule_config.hour,
      run_at_minute: taskData.schedule_config.minute,
      run_timezone: 'Asia/Shanghai'
    }
    
    let createdTask: any
    if (isEdit.value) {
      await taskStore.updateTask(taskId.value, { ...payload, status } as any)
      showToast('任务更新成功', 'success')
      router.push('/tasks')
    } else {
      createdTask = await taskStore.createTask(payload as any)
      
      // If startAfterCreate, start the task immediately
      if (startAfterCreate && createdTask?.id) {
        try {
          await taskStore.startTask(createdTask.id)
          showToast('任务创建并启动成功', 'success')
          router.push('/tasks')
        } catch (e: any) {
          // Task created but start failed
          showToast('任务创建成功，但启动失败: ' + (e.response?.data?.detail || e.response?.data?.error || '未知错误'), 'error', 5000)
          router.push('/tasks')
        }
      } else {
        showToast('任务创建成功', 'success')
        router.push('/tasks')
      }
    }
  } catch (e: any) {
    showToast(e.response?.data?.detail || (isEdit.value ? '保存任务失败' : '创建任务失败'), 'error')
  } finally {
    submitting.value = false
  }
}

</script>
