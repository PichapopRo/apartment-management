<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'
import StatCard from '../components/StatCard.vue'

type Room = {
  id?: number
  room_number: string
  status: 'vacant' | 'occupied' | 'maintenance'
  rent_rate?: number
}

const rooms = ref<Room[]>([])
const loading = ref(true)
const error = ref('')
const residentSummary = ref<{
  room: { room_number: string; rent_rate: number; status: string } | null
  latest_bill: { billing_month: string; total_amount: number; status: string; is_paid: boolean } | null
} | null>(null)

const loadRooms = async () => {
  loading.value = true
  error.value = ''
  try {
    if (authStore.user.value?.role === 'resident') {
      residentSummary.value = await apiClient.get('/resident/summary')
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
    </header>

    <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
    <div v-else>
      <div v-if="authStore.user.value?.role === 'resident'" class="grid gap-4 md:grid-cols-2">
        <StatCard
          label="Your Room"
          :value="residentSummary?.room?.room_number || '—'"
        />
        <StatCard
          label="Rent Amount"
          :value="residentSummary?.room?.rent_rate ? `${residentSummary?.room?.rent_rate.toLocaleString()} THB` : '—'"
        />
        <StatCard
          label="Bill Status"
          :value="residentSummary?.latest_bill?.is_paid ? 'Paid' : 'Unpaid'"
        />
        <StatCard
          label="Latest Bill"
          :value="residentSummary?.latest_bill?.total_amount ? `${residentSummary?.latest_bill?.total_amount.toLocaleString()} THB` : '—'"
        />
      </div>
      <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Rooms" :value="loading ? '...' : stats.total" />
        <StatCard label="Occupied" :value="loading ? '...' : stats.occupied" trend="+3 this month" />
        <StatCard label="Vacant" :value="loading ? '...' : stats.vacant" />
        <StatCard label="Maintenance" :value="loading ? '...' : stats.maintenance" />
      </div>
    </div>
  </section>
</template>
