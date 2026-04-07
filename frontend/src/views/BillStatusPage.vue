<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient } from '../utils/api'
import { authStore } from '../stores/auth'

type Room = { id: number; room_number: string }
type Bill = {
  id: number
  room_id: number
  billing_month: string
  total_amount: string | number
  is_paid: boolean
  paid_at?: string | null
  remark?: string | null
}

const rooms = ref<Room[]>([])
const billsByRoom = ref<Record<number, Bill | null>>({})
const month = ref('')
const error = ref('')
const loading = ref(false)

const canAccess = computed(() => {
  const role = authStore.user.value?.role
  return role === 'admin' || role === 'staff'
})

const loadRooms = async () => {
  rooms.value = await apiClient.get<Room[]>('/rooms')
}

const loadBills = async () => {
  if (!month.value) return
  loading.value = true
  error.value = ''
  try {
    const results = await Promise.all(
      rooms.value.map(async (room) => {
        try {
          const bill = await apiClient.get<Bill[]>(
            `/billing/bills?room_id=${room.id}&month=${month.value}`
          )
          return [room.id, bill[0] || null] as const
        } catch {
          return [room.id, null] as const
        }
      })
    )
    billsByRoom.value = Object.fromEntries(results)
  } catch (err) {
    error.value = 'Failed to load bills.'
  } finally {
    loading.value = false
  }
}

const updateBill = async (roomId: number, updates: Partial<Bill>) => {
  const bill = billsByRoom.value[roomId]
  if (!bill) return
  try {
    await apiClient.patch(`/billing/bills/${bill.id}`, {
      is_paid: updates.is_paid ?? bill.is_paid,
      paid_at: updates.is_paid ? new Date().toISOString() : null,
      remark: updates.remark ?? bill.remark
    })
    await loadBills()
  } catch (err) {
    error.value = 'Failed to update bill.'
  }
}

onMounted(async () => {
  await loadRooms()
})
</script>

<template>
  <section class="grid gap-4">
    <header class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold">Bill Status</h1>
        <p class="text-sm text-slate-500">Admin and staff only.</p>
      </div>
      <div class="flex items-center gap-3">
        <input v-model="month" type="month" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" @change="loadBills" />
      </div>
    </header>

    <div v-if="!canAccess" class="text-sm text-rose-600">You don’t have access to this page.</div>
    <div v-else>
      <div v-if="error" class="text-xs text-rose-600">{{ error }}</div>
      <div v-if="loading" class="text-xs text-slate-500">Loading...</div>

      <div class="overflow-auto rounded-2xl border border-slate-200 bg-white/80 shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-slate-50 text-left text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th class="px-4 py-3">Room</th>
              <th class="px-4 py-3">Total</th>
              <th class="px-4 py-3">Paid</th>
              <th class="px-4 py-3">Remark</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="room in rooms" :key="room.id" class="border-t border-slate-200">
              <td class="px-4 py-3 font-semibold text-slate-700">{{ room.room_number }}</td>
              <td class="px-4 py-3">{{ billsByRoom[room.id]?.total_amount ?? '—' }}</td>
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  :checked="billsByRoom[room.id]?.is_paid"
                  @change="updateBill(room.id, { is_paid: ($event.target as HTMLInputElement).checked })"
                  :disabled="!billsByRoom[room.id]"
                />
              </td>
              <td class="px-4 py-3">
                <input
                  class="w-64 rounded-lg border border-slate-200 px-2 py-1"
                  :value="billsByRoom[room.id]?.remark || ''"
                  @change="updateBill(room.id, { remark: ($event.target as HTMLInputElement).value })"
                  :disabled="!billsByRoom[room.id]"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>
