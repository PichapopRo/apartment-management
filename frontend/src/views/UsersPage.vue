<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'

type User = {
  id: number
  username: string
  email: string
  full_name?: string | null
  role: 'admin' | 'staff' | 'resident'
  is_active: boolean
}

const users = ref<User[]>([])
const loading = ref(false)
const error = ref('')

const loadUsers = async () => {
  loading.value = true
  error.value = ''
  try {
    users.value = await apiClient.get<User[]>('/auth/users')
  } catch (err) {
    error.value = 'Failed to load users.'
  } finally {
    loading.value = false
  }
}

const updateRole = async (user: User, role: User['role']) => {
  try {
    await apiClient.patch(`/auth/users/${user.id}/role`, { role })
    await loadUsers()
  } catch (err) {
    error.value = 'Failed to update role.'
  }
}

const deleteUser = async (user: User) => {
  if (!confirm(`Delete user ${user.username}?`)) return
  try {
    await apiClient.delete(`/auth/users/${user.id}`)
    await loadUsers()
  } catch (err) {
    error.value = 'Failed to delete user.'
  }
}

onMounted(loadUsers)
</script>

<template>
  <section class="grid gap-4">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Users</h1>
        <p class="text-sm text-slate-500">Admin only. Manage roles and access.</p>
      </div>
    </header>

    <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
    <div v-if="loading" class="text-xs text-slate-500">Loading...</div>

    <div class="overflow-auto rounded-2xl border border-slate-200 bg-white/80 shadow-sm">
      <table class="min-w-full text-sm">
        <thead class="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
          <tr>
            <th class="px-4 py-3">ID</th>
            <th class="px-4 py-3">Username</th>
            <th class="px-4 py-3">Email</th>
            <th class="px-4 py-3">Role</th>
            <th class="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" class="border-t border-slate-200">
            <td class="px-4 py-3 font-mono">{{ user.id }}</td>
            <td class="px-4 py-3">{{ user.username }}</td>
            <td class="px-4 py-3">{{ user.email }}</td>
            <td class="px-4 py-3">
              <select
                class="rounded-lg border border-slate-200 px-2 py-1 text-sm"
                :value="user.role"
                @change="updateRole(user, ($event.target as HTMLSelectElement).value as User['role'])"
                :disabled="user.id === 1"
              >
                <option value="admin">Admin</option>
                <option value="staff">Staff</option>
                <option value="resident">Resident</option>
              </select>
            </td>
            <td class="px-4 py-3">
              <button
                class="rounded-lg border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700"
                @click="deleteUser(user)"
                :disabled="user.id === 1"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
