/**
 * Clipboard utility functions
 */

export async function copyToClipboard(text: string): Promise<void> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      // Modern async clipboard API
      await navigator.clipboard.writeText(text)
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        document.execCommand('copy')
        textArea.remove()
      } catch (err) {
        textArea.remove()
        throw new Error('Failed to copy text')
      }
    }
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
    throw err
  }
}

export async function readFromClipboard(): Promise<string> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      return await navigator.clipboard.readText()
    } else {
      throw new Error('Clipboard API not available')
    }
  } catch (err) {
    console.error('Failed to read from clipboard:', err)
    throw err
  }
}
