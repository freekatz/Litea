import api from './client'
import type { RetrievalSource } from '@/types'

export const sourcesApi = {
  /**
   * List available retrieval sources
   */
  async list(): Promise<RetrievalSource[]> {
    const response = await api.get('/sources')
    return response.data.data
  }
}
