import { ref } from 'vue'
import { apiClient } from '../utils/api'

type User = {
  id: number
  username: string
  email: string
  role: 'admin' | 'staff' | 'resident'
  full_name?: string | null
}

const token = ref<string | null>(localStorage.getItem('token'))
const user = ref<User | null>(null)

const setToken = (value: string | null) => {
  token.value = value
  if (value) {
    localStorage.setItem('token', value)
  } else {
    localStorage.removeItem('token')
  }
}

const login = async (username: string, password: string) => {
  const form = new URLSearchParams()
  form.set('username', username)
  form.set('password', password)

  const res = await apiClient.postForm('/auth/login', form)
  setToken(res.access_token)
  await fetchMe()
}

const register = async (payload: {
  username: string
  email: string
  full_name?: string
  password: string
  role?: 'admin' | 'staff' | 'resident'
}) => {
  const body = {
    username: payload.username,
    email: payload.email,
    full_name: payload.full_name,
    password: payload.password,
    role: payload.role ?? ('resident' as const)
  }
  try {
    await apiClient.post('/auth/register', body)
    await login(payload.username, payload.password)
  } catch (err: any) {
    if (err instanceof Error) {
      throw err
    }
    throw err
  }
}

const fetchMe = async () => {
  user.value = await apiClient.get<User>('/auth/me')
}

const logout = () => {
  setToken(null)
  user.value = null
}

export const authStore = { token, user, login, register, fetchMe, logout }
