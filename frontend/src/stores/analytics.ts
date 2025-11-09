import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analyticsApi } from '@/api'
import type { TaskTrend, KeywordDistribution, SourceDistribution } from '@/types'

export const useAnalyticsStore = defineStore('analytics', () => {
  const trends = ref<TaskTrend[]>([])
  const keywords = ref<KeywordDistribution[]>([])
  const sources = ref<SourceDistribution[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTaskTrends(taskId: number, days: number = 30) {
    loading.value = true
    error.value = null
    try {
      trends.value = await analyticsApi.getTaskTrends(taskId, days)
      return trends.value
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取趋势数据失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchKeywordDistribution(taskId: number, limit: number = 20) {
    loading.value = true
    error.value = null
    try {
      keywords.value = await analyticsApi.getKeywordDistribution(taskId, limit)
      return keywords.value
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取关键词分布失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchSourceDistribution(taskId: number) {
    loading.value = true
    error.value = null
    try {
      sources.value = await analyticsApi.getSourceDistribution(taskId)
      return sources.value
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取来源分布失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchAllAnalytics(taskId: number, days: number = 30) {
    await Promise.all([
      fetchTaskTrends(taskId, days),
      fetchKeywordDistribution(taskId),
      fetchSourceDistribution(taskId)
    ])
  }

  return {
    trends,
    keywords,
    sources,
    loading,
    error,
    fetchTaskTrends,
    fetchKeywordDistribution,
    fetchSourceDistribution,
    fetchAllAnalytics
  }
})
