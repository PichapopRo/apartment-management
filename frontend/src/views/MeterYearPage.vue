<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'

type Room = { id: number; room_number: string }

type Reading = {
  id: number
  room_id: number
  billing_month: string
  water_value: string | number
  electric_value: string | number
}

const rooms = ref<Room[]>([])
const readingsByRoom = ref<Record<number, Reading[]>>({})
const year = ref(new Date().getFullYear())
const error = ref('')
const loading = ref(false)
const tab = ref<'water' | 'electric'>('water')

const canAccess = computed(() => {
  const role = authStore.user.value?.role
  return role === 'admin' || role === 'staff'
})

const years = computed(() => {
  const list: number[] = []
  for (let y = new Date().getFullYear(); y >= 2016; y -= 1) list.push(y)
  return list
})

const loadRooms = async () => {
  rooms.value = await apiClient.get<Room[]>('/rooms')
}

const loadReadings = async () => {
  loading.value = true
  error.value = ''
  try {
    const results = await Promise.all(
      rooms.value.map(async (room) => {
        const items = await apiClient.get<Reading[]>(
          `/billing/readings/year?room_id=${room.id}&year=${year.value}`
        )
        return [room.id, items] as const
      })
    )
    readingsByRoom.value = Object.fromEntries(results)
  } catch (err) {
    error.value = 'Failed to load yearly readings.'
  } finally {
    loading.value = false
  }
}

const months = computed(() => {
  return Array.from({ length: 12 }, (_, i) => {
    const m = i + 1
    return `${year.value}-${String(m).padStart(2, '0')}`
  })
})

const valueFor = (roomId: number, month: string) => {
  const list = readingsByRoom.value[roomId] || []
  const found = list.find((r) => r.billing_month === month)
  if (!found) return '—'
  const value = tab.value === 'water' ? found.water_value : found.electric_value
  const num = Number(value)
  return Number.isFinite(num) ? String(num) : String(value ?? '')
}

onMounted(async () => {
  await loadRooms()
  await loadReadings()
})
</script>

<template>
  <section class="grid gap-4">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">Yearly Meter View</h1>
        <p class="text-sm text-slate-500">Admin and staff only.</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <select v-model.number="year" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" @change="loadReadings">
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
        <button
          class="rounded-full px-4 py-2 text-sm font-semibold"
          :class="tab === 'water' ? 'bg-slate-900 text-white' : 'border border-slate-200 text-slate-700'"
          @click="tab = 'water'"
        >
          Water
        </button>
        <button
          class="rounded-full px-4 py-2 text-sm font-semibold"
          :class="tab === 'electric' ? 'bg-slate-900 text-white' : 'border border-slate-200 text-slate-700'"
          @click="tab = 'electric'"
        >
          Electricity
        </button>
      </div>
    </header>

    <div v-if="!canAccess" class="text-sm text-rose-600">You don’t have access to this page.</div>
    <div v-else>
      <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
      <div v-if="loading" class="text-xs text-slate-500">Loading readings...</div>

      <div class="overflow-auto rounded-2xl border border-slate-200 bg-white/80 shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th class="px-4 py-3">Room</th>
              <th v-for="m in months" :key="m" class="px-4 py-3">{{ m }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="room in rooms" :key="room.id" class="border-t border-slate-200">
              <td class="px-4 py-3 font-semibold text-slate-700">{{ room.room_number }}</td>
              <td v-for="m in months" :key="`${room.id}-${m}`" class="px-4 py-3 font-semibold text-slate-700">
                {{ valueFor(room.id, m) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
