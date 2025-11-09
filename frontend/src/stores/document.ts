import { defineStore } from 'pinia'
import { ref } from 'vue'
import { documentsApi } from '@/api'
import type { Document, DocumentFilters, PaginatedResponse } from '@/types'

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<Document[]>([])
  const currentDocument = ref<Document | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedIds = ref<Set<number>>(new Set())

  async function fetchDocuments(filters?: DocumentFilters) {
    loading.value = true
    error.value = null
    try {
      const response = await documentsApi.list(filters)
      documents.value = response.data
      total.value = response.total
      return response
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取文献列表失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchDocument(id: number) {
    loading.value = true
    error.value = null
    try {
      currentDocument.value = await documentsApi.get(id)
      return currentDocument.value
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取文献详情失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchDocumentDetail(id: number) {
    loading.value = true
    error.value = null
    try {
      return await documentsApi.getDetail(id)
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取文献元数据失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchTaskDocuments(taskId: number, filters?: any) {
    loading.value = true
    error.value = null
    try {
      const response = await documentsApi.listForTask(taskId, filters)
      documents.value = response.data
      total.value = response.total
      return response
    } catch (e: any) {
      error.value = e.response?.data?.error || '获取任务文献失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function exportToZotero(documentIds: number[], collectionName?: string) {
    loading.value = true
    error.value = null
    try {
      return await documentsApi.exportToZotero(documentIds, collectionName)
    } catch (e: any) {
      error.value = e.response?.data?.error || '导出到 Zotero 失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  function toggleSelection(id: number) {
    if (selectedIds.value.has(id)) {
      selectedIds.value.delete(id)
    } else {
      selectedIds.value.add(id)
    }
  }

  function selectAll() {
    documents.value.forEach(doc => selectedIds.value.add(doc.id))
  }

  function clearSelection() {
    selectedIds.value.clear()
  }

  return {
    documents,
    currentDocument,
    total,
    loading,
    error,
    selectedIds,
    fetchDocuments,
    fetchDocument,
    fetchDocumentDetail,
    fetchTaskDocuments,
    exportToZotero,
    toggleSelection,
    selectAll,
    clearSelection
  }
})
