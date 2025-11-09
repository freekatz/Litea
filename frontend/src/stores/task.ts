import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tasksApi } from '@/api'
import type { Task, TaskFormData } from '@/types'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeTasks = computed(() => 
    tasks.value.filter(t => t.status === 'active')
  )

  const pausedTasks = computed(() => 
    tasks.value.filter(t => t.status === 'paused')
  )

  async function fetchTasks() {
    loading.value = true
    error.value = null
    try {
      tasks.value = await tasksApi.list()
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取任务列表失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchTask(id: number) {
    loading.value = true
    error.value = null
    try {
      currentTask.value = await tasksApi.get(id)
      return currentTask.value
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取任务详情失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createTask(data: TaskFormData) {
    loading.value = true
    error.value = null
    try {
      const task = await tasksApi.create(data)
      tasks.value.push(task)
      return task
    } catch (e: any) {
      error.value = e.response?.data?.error || '创建任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateTask(id: number, data: Partial<TaskFormData>) {
    loading.value = true
    error.value = null
    try {
      const updated = await tasksApi.update(id, data)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updated
      }
      if (currentTask.value?.id === id) {
        currentTask.value = updated
      }
      return updated
    } catch (e: any) {
      error.value = e.response?.data?.error || '更新任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTask(id: number) {
    loading.value = true
    error.value = null
    try {
      await tasksApi.delete(id)
      tasks.value = tasks.value.filter(t => t.id !== id)
      if (currentTask.value?.id === id) {
        currentTask.value = null
      }
    } catch (e: any) {
      error.value = e.response?.data?.error || '删除任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function executeTask(id: number) {
    loading.value = true
    error.value = null
    try {
      const result = await tasksApi.execute(id)
      await fetchTask(id) // Refresh task data
      return result
    } catch (e: any) {
      error.value = e.response?.data?.error || '执行任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function extractKeywords(prompt: string) {
    loading.value = true
    error.value = null
    try {
      return await tasksApi.extractKeywords(prompt)
    } catch (e: any) {
      error.value = e.response?.data?.error || 'AI 关键词提取失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function startTask(id: number) {
    loading.value = true
    error.value = null
    try {
      const updated = await tasksApi.start(id)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updated
      }
      if (currentTask.value?.id === id) {
        currentTask.value = updated
      }
      return updated
    } catch (e: any) {
      error.value = e.response?.data?.error || '启动任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function stopTask(id: number) {
    loading.value = true
    error.value = null
    try {
      const updated = await tasksApi.stop(id)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updated
      }
      if (currentTask.value?.id === id) {
        currentTask.value = updated
      }
      return updated
    } catch (e: any) {
      error.value = e.response?.data?.error || '停止任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function restartTask(id: number, config: { run_at_hour?: number; notification_config?: any }) {
    loading.value = true
    error.value = null
    try {
      const updated = await tasksApi.restart(id, config)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updated
      }
      if (currentTask.value?.id === id) {
        currentTask.value = updated
      }
      return updated
    } catch (e: any) {
      error.value = e.response?.data?.error || '重启任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    activeTasks,
    pausedTasks,
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    deleteTask,
    executeTask,
    extractKeywords,
    startTask,
    stopTask,
    restartTask
  }
})
