import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'

/**
 * Format date string to readable format
 */
export function formatDate(date: string | Date | undefined, fmt: string = 'yyyy-MM-dd HH:mm'): string {
  if (!date) return '-'
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return format(dateObj, fmt, { locale: zhCN })
  } catch {
    return '-'
  }
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date | undefined): string {
  if (!date) return '-'
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    const now = new Date()
    const diffMs = now.getTime() - dateObj.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return formatDate(dateObj, 'yyyy-MM-dd')
  } catch {
    return '-'
  }
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

/**
 * Download file from blob
 */
export function downloadFile(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
