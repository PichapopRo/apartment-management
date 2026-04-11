<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authStore } from './stores/auth'

const route = useRoute()
const router = useRouter()

const isPublic = computed(() => Boolean(route.meta.public))
const userRole = computed(() => authStore.user.value?.role)
const isAdminOrStaff = computed(() => userRole.value === 'admin' || userRole.value === 'staff')
const isResident = computed(() => userRole.value === 'resident')
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div
    :class="[
      'min-h-screen grid',
      isPublic ? 'grid-cols-1' : 'grid-cols-[260px_1fr]'
    ]"
  >
    <div class="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_#f8fafc_0%,_#e2e8f0_45%,_#cbd5f5_100%)]" />

    <aside v-if="!isPublic" class="flex flex-col gap-5 bg-gradient-to-b from-slate-900 to-slate-800 px-6 py-7 text-slate-50">
      <div class="text-[22px] font-semibold">MK House</div>
      <div class="text-[11px] uppercase tracking-[0.22em] text-slate-400">Operations Console</div>

      <div class="self-start rounded-full bg-slate-800/80 px-3 py-1 text-[11px] uppercase tracking-[0.2em]">
        {{ userRole || '—' }}
      </div>

      <nav class="grid gap-2">
        <RouterLink
          to="/dashboard"
          class="rounded-xl border border-slate-700 px-3 py-2 text-sm transition hover:-translate-y-0.5 hover:border-slate-400"
          active-class="bg-slate-800/80 border-slate-300"
        >
          Dashboard
        </RouterLink>
        <RouterLink
          to="/rooms"
          class="rounded-xl border border-slate-700 px-3 py-2 text-sm transition hover:-translate-y-0.5 hover:border-slate-400"
          active-class="bg-slate-800/80 border-slate-300"
        >
          Rooms
        </RouterLink>
        <RouterLink
          v-if="isAdminOrStaff"
          to="/meters"
          class="rounded-xl border border-slate-700 px-3 py-2 text-sm transition hover:-translate-y-0.5 hover:border-slate-400"
          active-class="bg-slate-800/80 border-slate-300"
        >
          Meters
        </RouterLink>
        <RouterLink
          v-if="isAdminOrStaff"
          to="/meters/yearly"
          class="rounded-xl border border-slate-700 px-3 py-2 text-sm transition hover:-translate-y-0.5 hover:border-slate-400"
          active-class="bg-slate-800/80 border-slate-300"
        >
          Yearly Meters
        </RouterLink>
        <RouterLink
          v-if="isAdminOrStaff"
          to="/billing/calc"
          class="rounded-xl border border-slate-700 px-3 py-2 text-sm transition hover:-translate-y-0.5 hover:border-slate-400"
          active-class="bg-slate-800/80 border-slate-300"
        >
          Rent Calc
        </RouterLink>
        <RouterLink
          v-if="isAdminOrStaff"
          to="/billing/status"
          class="rounded-xl border border-slate-700 px-3 py-2 text-sm transition hover:-translate-y-0.5 hover:border-slate-400"
          active-class="bg-slate-800/80 border-slate-300"
        >
          Bill Status
        </RouterLink>
      </nav>

      <div class="mt-auto rounded-xl border border-slate-800 bg-slate-800/70 p-3 text-xs">
        <div class="text-slate-400">API</div>
        <div class="font-mono text-slate-200">{{ apiUrl }}</div>
      </div>

      <button
        class="mt-3 rounded-full border border-slate-500 px-3 py-2 text-sm text-slate-100 hover:border-slate-200"
        @click="logout"
      >
        Logout
      </button>
    </aside>

    <main class="p-8">
      <RouterView />
    </main>
  </div>
</template>
