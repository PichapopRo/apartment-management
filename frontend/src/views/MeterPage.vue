<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'

type Room = {
  id: number
  room_number: string
}

type Reading = {
  id: number
  room_id: number
  billing_month: string
  water_value: string | number
  electric_value: string | number
}

const rooms = ref<Room[]>([])
const readingsByRoom = ref<Record<number, Reading[]>>({})
const currentValues = ref<{
  water: Record<number, string>
  electric: Record<number, string>
}>({
  water: {},
  electric: {}
})
const month = ref('')
const error = ref('')
const tab = ref<'water' | 'electric'>('water')
const loading = ref(false)

const canAccess = computed(() => {
  const role = authStore.user.value?.role
  return role === 'admin' || role === 'staff'
})

const monthHeaders = computed(() => {
  if (!rooms.value.length) return [] as string[]
  const sample = readingsByRoom.value[rooms.value[0].id] || []
  return sample.slice(0, 6).map((r) => r.billing_month)
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
          `/billing/readings?room_id=${room.id}&limit=6`
        )
        return [room.id, items] as const
      })
    )
    readingsByRoom.value = Object.fromEntries(results)
  } catch (err) {
    error.value = 'Failed to load readings.'
  } finally {
    loading.value = false
  }
}

const submitAll = async () => {
  if (!month.value) {
    error.value = 'Billing month is required.'
    return
  }
  error.value = ''
  try {
    const missingRooms: string[] = []
    const invalidRooms: string[] = []
    const payloads = rooms.value.map((room) => {
      const waterRaw = currentValues.value.water[room.id]
      const electricRaw = currentValues.value.electric[room.id]

      if (waterRaw === undefined || waterRaw === '' || electricRaw === undefined || electricRaw === '') {
        missingRooms.push(room.room_number)
        return null
      }

      const waterVal = Number(waterRaw)
      const electricVal = Number(electricRaw)
      if (!Number.isFinite(waterVal) || !Number.isFinite(electricVal)) {
        invalidRooms.push(room.room_number)
        return null
      }

      const latest = (readingsByRoom.value[room.id] || [])[0]
      if (latest) {
        const prevWater = Number(latest.water_value)
        const prevElectric = Number(latest.electric_value)
        if (Number.isFinite(prevWater) && waterVal <= prevWater) {
          invalidRooms.push(room.room_number)
          return null
        }
        if (Number.isFinite(prevElectric) && electricVal <= prevElectric) {
          invalidRooms.push(room.room_number)
          return null
        }
      }

      return {
        room_id: room.id,
        billing_month: month.value,
        water_value: waterVal,
        electric_value: electricVal
      }
    }).filter((item): item is NonNullable<typeof item> => item !== null)

    if (missingRooms.length) {
      error.value = `Please fill water and electricity for: ${missingRooms.join(', ')}`
      return
    }
    if (invalidRooms.length) {
      error.value = `Values must be greater than previous month for: ${invalidRooms.join(', ')}`
      return
    }

    for (const payload of payloads) {
      await apiClient.post('/billing/readings', payload)
    }

    currentValues.value = { water: {}, electric: {} }
    await loadReadings()
  } catch (err) {
    error.value = 'Failed to save readings.'
  }
}

const formatValue = (reading: Reading) => {
  const value = tab.value === 'water' ? reading.water_value : reading.electric_value
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
        <h1 class="text-2xl font-semibold">Meter Readings</h1>
        <p class="text-sm text-slate-500">Admin and staff only.</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <input v-model="month" type="month" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
        <button
          class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
          @click="submitAll"
        >
          Save All
        </button>
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
              <th class="px-4 py-3">Current {{ tab === 'water' ? 'Water' : 'Electric' }}</th>
              <th v-for="m in monthHeaders" :key="m" class="px-4 py-3">{{ m }}</th>
              <th v-for="n in Math.max(0, 6 - monthHeaders.length)" :key="`empty-h-${n}`" class="px-4 py-3">—</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="room in rooms" :key="room.id" class="border-t border-slate-200">
              <td class="px-4 py-3 font-semibold text-slate-700">{{ room.room_number }}</td>
              <td class="px-4 py-3">
                <input
                  v-model="currentValues[tab][room.id]"
                  type="number"
                  class="w-28 rounded-lg border border-slate-200 px-2 py-1"
                />
              </td>
              <template v-for="(reading, idx) in (readingsByRoom[room.id] || [])" :key="reading.id">
                <td v-if="idx < 6" class="px-4 py-3">
                  <div class="font-semibold text-slate-700">{{ formatValue(reading) }}</div>
                </td>
              </template>
              <template v-for="n in Math.max(0, 6 - ((readingsByRoom[room.id] || []).length))" :key="`empty-${room.id}-${n}`">
                <td class="px-4 py-3 text-slate-400">—</td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
