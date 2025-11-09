import api from './client'

export const analyticsApi = {
  async getOverview() {
    const response = await api.get('/analytics/overview')
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
