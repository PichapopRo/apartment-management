import { authStore } from '../stores/auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  body?: BodyInit | null
  headers?: Record<string, string>
}

const request = async <T>(path: string, options: RequestOptions = {}) => {
  const headers: Record<string, string> = options.headers ? { ...options.headers } : {}
  if (authStore.token.value) {
    headers.Authorization = `Bearer ${authStore.token.value}`
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ?? null
  })

  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(errorText || `Request failed with ${res.status}`)
  }

  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return res.json() as Promise<T>
  }
  return (await res.text()) as T
}

const requestBlob = async (path: string) => {
  const headers: Record<string, string> = {}
  if (authStore.token.value) {
    headers.Authorization = `Bearer ${authStore.token.value}`
  }
  const res = await fetch(`${API_URL}${path}`, { method: 'GET', headers })
  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(errorText || `Request failed with ${res.status}`)
  }
  return res.blob()
}

const requestBlobPost = async (path: string, data: unknown) => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (authStore.token.value) {
    headers.Authorization = `Bearer ${authStore.token.value}`
  }
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data)
  })
  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(errorText || `Request failed with ${res.status}`)
  }
  return res.blob()
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data: unknown) =>
    request<T>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),
  delete: <T>(path: string) =>
    request<T>(path, {
      method: 'DELETE'
    }),
  patch: <T>(path: string, data: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),
  put: <T>(path: string, data: unknown) =>
    request<T>(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),
  postForm: <T>(path: string, data: URLSearchParams) =>
    request<T>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: data.toString()
    }),
  getBlob: (path: string) => requestBlob(path),
  postBlob: (path: string, data: unknown) => requestBlobPost(path, data),
  postFile: <T>(path: string, formData: FormData) =>
    request<T>(path, {
      method: 'POST',
      body: formData
    })
}
