import api from './client'

export const documentsApi = {
  async list(filters?: any) {
    const response = await api.get('/documents', { params: filters })
    return response.data
  },

  async get(id: number) {
    const response = await api.get(`/documents/${id}`)
    return response.data
  },

  async getDetail(id: number) {
    const response = await api.get(`/documents/${id}/detail`)
    return response.data
  },

  async listForTask(taskId: number, filters?: any) {
    const response = await api.get(`/tasks/${taskId}/documents`, { params: filters })
    return response.data
  },

  async exportToZotero(documentIds: number[], collectionName?: string) {
    const response = await api.post('/documents/export/zotero', {
      document_ids: documentIds,
      collection_name: collectionName
    })
    return response.data
  }
}
