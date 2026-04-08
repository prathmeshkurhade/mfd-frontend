import axios from 'axios'
import { supabase } from './supabase'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const { error: refreshError } = await supabase.auth.refreshSession()
      if (refreshError) {
        await supabase.auth.signOut()
        window.location.href = '/login'
        return Promise.reject(error)
      }
      // Retry the original request with new token
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        error.config.headers.Authorization = `Bearer ${session.access_token}`
        return apiClient(error.config)
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
