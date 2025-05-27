// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Generic API call function
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
    },
  }

  const response = await fetch(url, {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API call failed: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Perks API functions
export const perksApi = {
  // Get all perks
  getPerks: async () => {
    return apiCall('/api/perks')
  },

  // Get single perk by ID
  getPerk: async (id: number) => {
    return apiCall(`/api/perks/${id}`)
  },

  // Add new perk
  addPerk: async (perkData: {
    name: string
    url: string
    category?: string
    description?: string
  }) => {
    return apiCall('/api/perks', {
      method: 'POST',
      body: JSON.stringify(perkData)
    })
  },

  // Update perk
  updatePerk: async (id: number, perkData: any) => {
    return apiCall(`/api/perks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(perkData)
    })
  },

  // Delete perk
  deletePerk: async (id: number) => {
    return apiCall(`/api/perks/${id}`, {
      method: 'DELETE'
    })
  },

  // Run scraper for all perks
  runScraper: async () => {
    return apiCall('/api/perks/scrape', {
      method: 'POST'
    })
  },

  // Run scraper for specific perk
  scrapePerk: async (id: number) => {
    return apiCall(`/api/perks/${id}/scrape`, {
      method: 'POST'
    })
  },

  // Get scraper status
  getScraperStatus: async () => {
    return apiCall('/api/perks/scraper-status')
  }
}

// Pitchdecks API functions
export const pitchdecksApi = {
  // Get all applications
  getApplications: async (filters?: {
    status?: string
    sector?: string
    search?: string
  }) => {
    const params = new URLSearchParams()
    if (filters?.status) params.append('status', filters.status)
    if (filters?.sector) params.append('sector', filters.sector)
    if (filters?.search) params.append('search', filters.search)
    
    const queryString = params.toString()
    return apiCall(`/api/pitchdecks${queryString ? `?${queryString}` : ''}`)
  },

  // Get single application by ID
  getApplication: async (id: number) => {
    return apiCall(`/api/pitchdecks/${id}`)
  },

  // Upload new application
  uploadApplication: async (formData: FormData) => {
    return fetch(`${API_BASE_URL}/api/pitchdecks/upload`, {
      method: 'POST',
      body: formData
    }).then(response => {
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`)
      }
      return response.json()
    })
  },

  // Analyze application
  analyzeApplication: async (id: number) => {
    return apiCall(`/api/pitchdecks/${id}/analyze`, {
      method: 'POST'
    })
  },

  // Analyze multiple applications
  analyzeBatch: async (ids: number[]) => {
    return apiCall('/api/pitchdecks/analyze-batch', {
      method: 'POST',
      body: JSON.stringify({ application_ids: ids })
    })
  },

  // Update review status
  updateReviewStatus: async (id: number, status: 'approved' | 'rejected' | 'pending') => {
    return apiCall(`/api/pitchdecks/${id}/review`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    })
  },

  // Add comment
  addComment: async (id: number, comment: string) => {
    return apiCall(`/api/pitchdecks/${id}/comments`, {
      method: 'POST',
      body: JSON.stringify({ comment })
    })
  },

  // Get analysis status
  getAnalysisStatus: async (id: number) => {
    return apiCall(`/api/pitchdecks/${id}/analysis-status`)
  }
}

// System API functions
export const systemApi = {
  // Get system status
  getStatus: async () => {
    return apiCall('/api/system/status')
  },

  // Get dashboard stats
  getDashboardStats: async () => {
    return apiCall('/api/dashboard/stats')
  },

  // Get recent activity
  getRecentActivity: async () => {
    return apiCall('/api/dashboard/activity')
  },

  // Get logs
  getLogs: async (service: string, limit?: number) => {
    const params = new URLSearchParams()
    if (limit) params.append('limit', limit.toString())
    
    return apiCall(`/api/logs/${service}${params.toString() ? `?${params.toString()}` : ''}`)
  }
}

// Utility function for handling API errors
export const handleApiError = (error: any) => {
  console.error('API Error:', error)
  
  if (error.message.includes('Failed to fetch')) {
    return 'Unable to connect to server. Please check your connection.'
  }
  
  if (error.message.includes('404')) {
    return 'Resource not found.'
  }
  
  if (error.message.includes('401')) {
    return 'Unauthorized access. Please check your credentials.'
  }
  
  if (error.message.includes('500')) {
    return 'Server error. Please try again later.'
  }
  
  return error.message || 'An unexpected error occurred.'
}

// Type definitions for API responses
export interface Perk {
  id: number
  name: string
  category: string
  status: string
  lastUpdated: string
  url: string
  requirements: string
  value: string
  applicationWindow: string
  availability: string
}

export interface Application {
  id: number
  teamName: string
  companyName: string
  submissionDate: string
  status: string
  aiScore: number | null
  humanReview: string
  stage: string
  sector: string
  fundingAsked: string
  pitchDeckUrl: string
  analysisStatus: string
}

export interface DashboardStats {
  perks: {
    total: number
    lastUpdated: string
    successfulUpdates: number
    failedUpdates: number
  }
  pitchdecks: {
    total: number
    pending: number
    analyzed: number
    approved: number
    rejected: number
  }
}

export interface SystemStatus {
  perks_scraper: 'operational' | 'error' | 'maintenance'
  pitchdeck_analyzer: 'operational' | 'error' | 'maintenance'
  database: 'operational' | 'error' | 'maintenance'
  api: 'operational' | 'error' | 'maintenance'
} 