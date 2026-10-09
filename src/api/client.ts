import axios from 'axios'
import toast from 'react-hot-toast'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

apiClient.interceptors.request.use((config) => {
  const raw = localStorage.getItem('auth_token')
  if (raw) {
    try {
      const token = JSON.parse(raw)
      if (token?.token) config.headers.Authorization = `Bearer ${token.token}`
    } catch {
      // ignore malformed token
    }
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.message || error?.message || 'Something went wrong. Please try again.'
    toast.error(message)
    return Promise.reject(error)
  },
)

export default apiClient
