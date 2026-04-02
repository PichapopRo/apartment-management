<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import StatCard from '../components/StatCard.vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'

type Room = {
  id?: number
  room_number: string
  status: 'vacant' | 'occupied' | 'maintenance'
  rent_rate?: number
}

const rooms = ref<Room[]>([])
const loading = ref(true)
const error = ref('')

const loadRooms = async () => {
  loading.value = true
  error.value = ''
  try {
    if (authStore.user.value?.role === 'resident') {
      rooms.value = await apiClient.get<Room[]>('/rooms/public')
    } else {
      rooms.value = await apiClient.get<Room[]>('/rooms')
    }
  } catch (err) {
    error.value = 'Failed to load room stats.'
  } finally {
    loading.value = false
  }
}

onMounted(loadRooms)

const stats = computed(() => {
  const total = rooms.value.length
  const occupied = rooms.value.filter((r) => r.status === 'occupied').length
  const vacant = rooms.value.filter((r) => r.status === 'vacant').length
  const maintenance = rooms.value.filter((r) => r.status === 'maintenance').length
  return { total, occupied, vacant, maintenance }
})
</script>

<template>
  <section class="grid gap-6">
    <header>
      <h1 class="text-2xl font-semibold">Dashboard</h1>
      <p class="text-sm text-slate-500">Live occupancy snapshot from the backend.</p>
    </header>

    <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
    <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <StatCard label="Total Rooms" :value="loading ? '...' : stats.total" />
      <StatCard label="Occupied" :value="loading ? '...' : stats.occupied" trend="+3 this month" />
      <StatCard label="Vacant" :value="loading ? '...' : stats.vacant" />
      <StatCard label="Maintenance" :value="loading ? '...' : stats.maintenance" />
    </div>
  </section>
</template>
