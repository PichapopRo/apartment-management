<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../stores/auth'

const router = useRouter()
const form = ref({
  username: '',
  email: '',
  full_name: '',
  password: '',
  role: 'admin' as 'admin' | 'staff' | 'resident'
})
const error = ref('')

const submit = async () => {
  error.value = ''
  try {
    await authStore.register(form.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = 'Registration failed. Admin bootstrap may already be used.'
  }
}
</script>

<template>
  <div class="grid min-h-screen place-items-center px-4">
    <div class="grid w-full max-w-lg gap-3 rounded-2xl border border-slate-200/70 bg-white/85 p-8 shadow-2xl">
      <div>
        <h1 class="text-2xl font-semibold">Create admin account</h1>
        <p class="text-sm text-slate-500">Only the first registration can be admin.</p>
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
        <label class="grid gap-1 text-xs font-semibold text-slate-600">
          Role
          <select v-model="form.role" class="rounded-xl border border-slate-200 px-3 py-2">
            <option value="admin">Admin</option>
          </select>
        </label>
        <button
          type="submit"
          class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
        >
          Create Account
        </button>
        <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
      </form>
      <div class="text-xs text-slate-500">
        Already have an account? <router-link class="text-slate-900 underline" to="/login">Sign in</router-link>
      </div>
    </div>
  </div>
</template>
