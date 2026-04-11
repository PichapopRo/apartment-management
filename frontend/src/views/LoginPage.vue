<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../stores/auth'
import { apiClient } from '../utils/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const hasAdmin = ref(false)

const loadBootstrap = async () => {
  try {
    const res = await apiClient.get<{ admin_exists: boolean }>('/auth/bootstrap')
    hasAdmin.value = res.admin_exists
  } catch {
    hasAdmin.value = true
  }
}

const submit = async () => {
  error.value = ''
  try {
    await authStore.login(username.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = 'Login failed. Please check your credentials.'
  }
}

onMounted(loadBootstrap)
</script>

<template>
  <div class="grid min-h-screen place-items-center px-4">
    <div class="grid w-full max-w-md gap-3 rounded-2xl border border-slate-200/70 bg-white/85 p-8 shadow-2xl">
      <div>
        <h1 class="text-2xl font-semibold">Welcome back</h1>
        <p class="text-sm text-slate-500">Sign in to manage rooms and tenants.</p>
      </div>
      <form class="grid gap-3" @submit.prevent="submit">
        <label class="grid gap-1 text-xs font-semibold text-slate-600">
          Username
          <input v-model="username" class="rounded-xl border border-slate-200 px-3 py-2" placeholder="admin" />
        </label>
        <label class="grid gap-1 text-xs font-semibold text-slate-600">
          Password
          <input
            v-model="password"
            type="password"
            class="rounded-xl border border-slate-200 px-3 py-2"
            placeholder="????????"
          />
        </label>
        <button
          type="submit"
          class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
        >
          Sign In
        </button>
        <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
      </form>
      <div class="text-xs text-slate-500">
        First time?
        <router-link class="text-slate-900 underline" to="/register">
          {{ hasAdmin ? 'Create account' : 'Create admin account' }}
        </router-link>
      </div>
    </div>
  </div>
</template>
