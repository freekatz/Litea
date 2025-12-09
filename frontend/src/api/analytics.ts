import api from './client'

export const analyticsApi = {
  async getOverview(taskId?: number) {
    const params: Record<string, unknown> = {}
    if (taskId) params.task_id = taskId
    const response = await api.get('/analytics/overview', { params })
    return response.data
  },

  async getTrends(days: number = 7, taskId?: number) {
    const params: Record<string, unknown> = { days }
    if (taskId) params.task_id = taskId
    const response = await api.get('/analytics/trends', { params })
    return response.data
  },

  async getSources(taskId?: number) {
    const params: Record<string, unknown> = {}
    if (taskId) params.task_id = taskId
    const response = await api.get('/analytics/sources', { params })
    return response.data
  },

  async getScores(taskId?: number) {
    const params: Record<string, unknown> = {}
    if (taskId) params.task_id = taskId
    const response = await api.get('/analytics/scores', { params })
    return response.data
  },

  async getTaskTrends(taskId: number, days: number = 30) {
    const response = await api.get(`/analytics/tasks/${taskId}/trends`, {
      params: { days }
    })
    return response.data
  },

  async getKeywordDistribution(taskId: number, limit: number = 20) {
    const response = await api.get(`/analytics/tasks/${taskId}/keywords`, {
      params: { limit }
    })
    return response.data
  },

  async getSourceDistribution(taskId: number) {
    const response = await api.get(`/analytics/tasks/${taskId}/sources`)
    return response.data
  }
}
