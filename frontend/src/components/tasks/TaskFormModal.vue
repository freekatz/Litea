<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
      <div class="px-6 py-4 border-b flex items-center justify-between bg-gray-50">
        <h2 class="text-lg font-semibold">{{ task ? '编辑任务' : '创建新任务' }}</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">✕</button>
      </div>

      <form @submit.prevent="handleSubmit" class="px-6 py-4 overflow-y-auto max-h-[calc(90vh-8rem)]">
        <div class="space-y-4">
          <!-- 任务名称 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">任务名称 *</label>
            <input
              v-model="form.name"
              type="text"
              required
              placeholder="例如：追踪大语言模型最新研究"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          <!-- 研究主题 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">研究主题 (Prompt) *</label>
            <textarea
              v-model="form.prompt"
              required
              rows="3"
              placeholder="描述你的研究兴趣，AI将据此筛选文献"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            ></textarea>
            <button
              type="button"
              @click="extractKeywords"
              :disabled="!form.prompt || extracting"
              class="mt-2 text-sm text-primary-600 hover:text-primary-700 disabled:text-gray-400"
            >
              {{ extracting ? '提取中...' : '🤖 AI 提取关键词' }}
            </button>
          </div>

          <!-- 关键词 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">关键词</label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newKeyword"
                @keyup.enter="addKeyword"
                type="text"
                placeholder="输入关键词后按回车添加"
                class="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500"
              />
              <button
                type="button"
                @click="addKeyword"
                class="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >添加</button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(kw, idx) in form.keywords"
                :key="idx"
                class="inline-flex items-center gap-1 px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm"
              >
                {{ kw.keyword }}
                <button type="button" @click="removeKeyword(idx)" class="hover:text-primary-900">×</button>
              </span>
            </div>
          </div>

          <!-- 数据源 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">数据源 *</label>
            <div class="space-y-2">
              <label class="flex items-center gap-2">
                <input
                  type="checkbox"
                  v-model="sourceArxiv"
                  class="rounded text-primary-600"
                />
                <span class="text-sm">arXiv</span>
              </label>
            </div>
          </div>

          <!-- 执行时间 -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">执行时间 *</label>
              <div class="flex gap-2">
                <input
                  v-model.number="form.run_at_hour"
                  type="number"
                  min="0"
                  max="23"
                  required
                  class="w-20 px-3 py-2 border border-gray-300 rounded"
                />
                <span class="py-2">:</span>
                <input
                  v-model.number="form.run_at_minute"
                  type="number"
                  min="0"
                  max="59"
                  required
                  class="w-20 px-3 py-2 border border-gray-300 rounded"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">时区</label>
              <input
                v-model="form.run_timezone"
                type="text"
                value="Asia/Shanghai"
                class="w-full px-3 py-2 border border-gray-300 rounded bg-gray-50"
                readonly
              />
            </div>
          </div>

          <!-- 通知设置 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮件通知</label>
            <input
              v-model="notificationEmail"
              type="email"
              placeholder="your@email.com"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-1 focus:ring-primary-500"
            />
          </div>
        </div>
      </form>

      <div class="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
        <button
          type="button"
          @click="$emit('close')"
          class="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
        >取消</button>
        <button
          type="submit"
          @click="handleSubmit"
          :disabled="!canSubmit"
          class="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >{{ task ? '保存' : '创建' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { tasksApi } from '@/api/tasks'
import type { Task } from '@/types'

const props = defineProps<{
  task?: Task | null
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const form = ref({
  name: '',
  prompt: '',
  keywords: [] as Array<{ keyword: string; is_user_defined: boolean }>,
  sources: [] as Array<{ source_name: string; parameters: any }>,
  run_at_hour: 9,
  run_at_minute: 0,
  run_timezone: 'Asia/Shanghai',
  notification: {
    channel: 'email',
    recipients: [] as string[],
  },
})

const newKeyword = ref('')
const notificationEmail = ref('')
const sourceArxiv = ref(true)
const extracting = ref(false)

const canSubmit = computed(() => {
  return form.value.name && form.value.prompt && (sourceArxiv.value)
})

function addKeyword() {
  if (newKeyword.value.trim()) {
    form.value.keywords.push({
      keyword: newKeyword.value.trim(),
      is_user_defined: true,
    })
    newKeyword.value = ''
  }
}

function removeKeyword(index: number) {
  form.value.keywords.splice(index, 1)
}

async function extractKeywords() {
  if (!form.value.prompt) return
  extracting.value = true
  try {
    const response = await tasksApi.suggestKeywords({
      prompt: form.value.prompt,
      max_keywords: 10,
    })
    const suggested = response.data.data
    suggested.forEach((kw: string) => {
      if (!form.value.keywords.find(k => k.keyword === kw)) {
        form.value.keywords.push({ keyword: kw, is_user_defined: false })
      }
    })
  } catch (error) {
    console.error('Failed to extract keywords:', error)
  } finally {
    extracting.value = false
  }
}

async function handleSubmit() {
  if (!canSubmit.value) return

  // 准备数据源
  form.value.sources = []
  if (sourceArxiv.value) {
    form.value.sources.push({
      source_name: 'arxiv',
      parameters: {},
    })
  }

  // 准备通知
  if (notificationEmail.value) {
    form.value.notification.recipients = [notificationEmail.value]
  }

  try {
    if (props.task) {
      await tasksApi.update(props.task.id, form.value)
    } else {
      await tasksApi.create(form.value)
    }
    emit('saved')
  } catch (error) {
    console.error('Failed to save task:', error)
    alert('保存失败，请重试')
  }
}

onMounted(() => {
  if (props.task) {
    form.value = {
      name: props.task.name,
      prompt: props.task.prompt,
      keywords: [...props.task.keywords],
      sources: [...props.task.sources],
      run_at_hour: props.task.run_at_hour || 9,
      run_at_minute: props.task.run_at_minute || 0,
      run_timezone: props.task.run_timezone || 'Asia/Shanghai',
      notification: { ...props.task.notification },
    }
    notificationEmail.value = props.task.notification.recipients[0] || ''
    sourceArxiv.value = props.task.sources.some(s => s.source_name === 'arxiv')
  }
})
</script>
