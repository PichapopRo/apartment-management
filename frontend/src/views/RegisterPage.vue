<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../stores/auth'
import { apiClient } from '../utils/api'

const router = useRouter()
const isBootstrap = ref(true)
const form = ref({
  username: '',
  email: '',
  full_name: '',
  password: '',
  role: 'resident' as 'admin' | 'staff' | 'resident'
})
const error = ref('')

const loadBootstrap = async () => {
  try {
    const res = await apiClient.get<{ admin_exists: boolean }>('/auth/bootstrap')
    isBootstrap.value = !res.admin_exists
    form.value.role = isBootstrap.value ? 'admin' : 'resident'
  } catch {
    isBootstrap.value = true
    form.value.role = 'admin'
  }
}

const submit = async () => {
  error.value = ''
  try {
    await authStore.register(form.value)
    router.push('/dashboard')
  } catch (err) {
    const message = (err as Error)?.message
    if (message && message.startsWith('{')) {
      try {
        const parsed = JSON.parse(message)
        if (parsed?.errors?.length) {
          const messages = parsed.errors.map((e: any) => {
            const loc = String(e.loc || '')
            if (loc.includes('password')) {
              return 'Password must be at least 8 characters.'
            }
            if (loc.includes('email')) {
              return 'Email is invalid.'
            }
            if (loc.includes('username')) {
              return e.msg ? `Username ${e.msg.toLowerCase()}` : 'Username is invalid.'
            }
            return e.msg || 'Invalid input.'
          })
          error.value = messages.join('; ')
          return
        }
        if (parsed?.detail) {
          error.value = parsed.detail
          return
        }
      } catch {
        // fallthrough
      }
    }
    error.value = message || (isBootstrap.value
      ? 'Registration failed. Admin bootstrap may already be used.'
      : 'Registration failed.')
  }
}

onMounted(loadBootstrap)
</script>

<template>
  <div class="grid min-h-screen place-items-center px-4">
    <div class="grid w-full max-w-lg gap-3 rounded-2xl border border-slate-200/70 bg-white/85 p-8 shadow-2xl">
      <div>
        <h1 class="text-2xl font-semibold">
          {{ isBootstrap ? 'Create admin account' : 'Create account' }}
        </h1>
        <p class="text-sm text-slate-500">
          {{ isBootstrap ? 'Only the first registration can be admin.' : 'Register as a resident.' }}
        </p>
      </div>
      <form class="grid gap-3" @submit.prevent="submit">
        <label class="grid gap-1 text-xs font-semibold text-slate-600">
          Username
          <input v-model="form.username" class="rounded-xl border border-slate-200 px-3 py-2" placeholder="admin" />
        </label>
        <label class="grid gap-1 text-xs font-semibold text-slate-600">
          Email
          <input v-model="form.email" type="email" class="rounded-xl border border-slate-200 px-3 py-2" />
        </label>
        <label class="grid gap-1 text-xs font-semibold text-slate-600">
          Full name
          <input v-model="form.full_name" class="rounded-xl border border-slate-200 px-3 py-2" />
        </label>
        <label class="grid gap-1 text-xs font-semibold text-slate-600">
          Password
          <input v-model="form.password" type="password" class="rounded-xl border border-slate-200 px-3 py-2" />
        </label>
        <button
          type="submit"
          class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
        >
          {{ isBootstrap ? 'Create Admin' : 'Create Account' }}
        </button>
        <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
      </form>
      <div class="text-xs text-slate-500">
        Already have an account? <router-link class="text-slate-900 underline" to="/login">Sign in</router-link>
      </div>
    </div>
  </div>
</template>
