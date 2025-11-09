import api from './client'

export const tasksApi = {
  async list() {
    const response = await api.get('/tasks')
    return response.data
  },

  async listArchived() {
    const response = await api.get('/tasks/archived')
    return response.data
  },

  async get(id: number) {
    const response = await api.get(`/tasks/${id}`)
    return response.data
  },

  async create(data: any) {
    const response = await api.post('/tasks', data)
    return response.data
  },

  async update(id: number, data: any) {
    const response = await api.put(`/tasks/${id}`, data)
    return response.data
  },

  async delete(id: number) {
    // Note: This now permanently deletes the task and its documents
    await api.delete(`/tasks/${id}`)
  },

  async archive(id: number) {
    // Archive task without deleting it or its documents
    const response = await api.post(`/tasks/${id}/archive`)
    return response.data
  },

  async suggestKeywords(params: { prompt: string; max_keywords?: number }) {
    const response = await api.post('/tasks/keywords/suggest', params)
    return response.data
  },

  async start(id: number) {
    const response = await api.post(`/tasks/${id}/start`)
    return response.data
  },

  async stop(id: number) {
    const response = await api.post(`/tasks/${id}/stop`)
    return response.data
  },

  async restart(id: number, config: any) {
    const response = await api.post(`/tasks/${id}/restart`, config)
    return response.data
  }
}
