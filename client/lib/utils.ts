import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date) {
  const d = new Date(date)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatRelativeTime(date: string | Date) {
  const d = new Date(date)
  const now = new Date()
  const diffInMinutes = Math.floor((now.getTime() - d.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 1) return 'Just now'
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
  return `${Math.floor(diffInMinutes / 1440)}d ago`
}

export function getStatusColor(status: string) {
  switch (status.toLowerCase()) {
    case 'active':
    case 'approved':
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'pending':
    case 'analyzing':
      return 'bg-yellow-100 text-yellow-800'
    case 'error':
    case 'failed':
    case 'rejected':
      return 'bg-red-100 text-red-800'
    case 'expired':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-blue-100 text-blue-800'
  }
} 