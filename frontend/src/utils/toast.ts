/**
 * Simple toast notification utility
 */

type ToastType = 'success' | 'error' | 'info' | 'warning'

export function showToast(message: string, type: ToastType = 'info', duration: number = 3000) {
  // Create toast element
  const toast = document.createElement('div')
  toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-50 transition-opacity duration-300 ${getToastColor(type)}`
  toast.textContent = message
  toast.style.opacity = '0'
  
  // Add to DOM
  document.body.appendChild(toast)
  
  // Fade in
  setTimeout(() => {
    toast.style.opacity = '1'
  }, 10)
  
  // Fade out and remove
  setTimeout(() => {
    toast.style.opacity = '0'
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, duration)
}

function getToastColor(type: ToastType): string {
  switch (type) {
    case 'success':
      return 'bg-green-600'
    case 'error':
      return 'bg-red-600'
    case 'warning':
      return 'bg-yellow-600'
    case 'info':
    default:
      return 'bg-blue-600'
  }
}
